import argparse, os
import cv2, numpy as np
from scipy.spatial.distance import directed_hausdorff
from scipy.ndimage import distance_transform_edt
from skimage.metrics import structural_similarity as sk_ssim


def load_map(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Không đọc được: {path}")
    return img, img < 150, img > 200


def crop_to_content(occ, pad=10):
    rows = np.any(occ, axis=1); cols = np.any(occ, axis=0)
    if not rows.any(): return occ, (0, 0)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    r0 = max(0, r0-pad); r1 = min(occ.shape[0], r1+pad)
    c0 = max(0, c0-pad); c1 = min(occ.shape[1], c1+pad)
    return occ[r0:r1, c0:c1], (r0, c0)


def rotate_map(gray, angle):
    """Rotate grayscale map. Border = 205 (unknown), KHÔNG phải obstacle."""
    h, w = gray.shape
    cx, cy = w//2, h//2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    cos_a = abs(M[0, 0]); sin_a = abs(M[0, 1])
    new_w = int(h*sin_a + w*cos_a)
    new_h = int(h*cos_a + w*sin_a)
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2
    # borderValue=205: vùng ngoài = unknown, không phải obstacle (< 150)
    return cv2.warpAffine(gray, M, (new_w, new_h),
                          flags=cv2.INTER_NEAREST, borderValue=205)


def occ_from_gray(gray):
    return gray < 150


def match_score(big, small):
    if big.shape[0] < small.shape[0] or big.shape[1] < small.shape[1]:
        return -1.0, None
    res = cv2.matchTemplate(big.astype(np.float32),
                            small.astype(np.float32),
                            cv2.TM_CCOEFF_NORMED)
    score = float(res.max())
    _, _, _, loc = cv2.minMaxLoc(res)
    return score, loc


def align_maps(slam_gray, gt_gray, angle_step=5, angle_refine_step=1,
               angle_min=0, angle_max=360):
    gt_occ = occ_from_gray(gt_gray)
    sl_occ = occ_from_gray(slam_gray)
    h_gt, w_gt = gt_gray.shape

    # Tự động ước tính scale range từ số obstacle pixel
    sl_obs = sl_occ.sum(); gt_obs = gt_occ.sum()
    ratio = (gt_obs / sl_obs) ** 0.5 if sl_obs > 0 and gt_obs > 0 else 1.0
    scale_min = max(0.3,  ratio * 0.4)
    scale_max = min(10.0, ratio * 2.5)
    scale_step = 0.05
    print(f"  Scale range tự động: [{scale_min:.2f}, {scale_max:.2f}]  (ratio≈{ratio:.2f})")

    # Crop obstacle content để tăng tốc
    gt_crop_occ, _ = crop_to_content(gt_occ)
    gt_u8c = gt_crop_occ.astype(np.uint8) * 255
    K = np.ones((11, 11), np.uint8)
    gt_d = cv2.dilate(gt_u8c, K, iterations=3)
    h_g, w_g = gt_d.shape
    gt_area = float(h_g * w_g)

    print(f"  Coarse search (angle step={angle_step}°, scale step={scale_step})...")
    best_score, best_angle, best_scale = -1.0, 0, 1.0

    for angle in range(angle_min, angle_max, angle_step):
        # Rotate ảnh gray gốc, sau đó trích obstacle mask (đúng threshold)
        rot_gray = rotate_map(slam_gray, angle)
        rot_occ  = occ_from_gray(rot_gray)
        rot_crop, _ = crop_to_content(rot_occ)
        rot_crop_u8 = rot_crop.astype(np.uint8) * 255
        rot_d = cv2.dilate(rot_crop_u8, K, iterations=3)
        h_r, w_r = rot_d.shape

        for scale in np.arange(scale_min, scale_max + scale_step, scale_step):
            nh = int(h_r * scale); nw = int(w_r * scale)
            if nh < 10 or nw < 10: continue
            # Bỏ qua template quá nhỏ → tránh degenerate NCC=1.0
            if (nh * nw) / gt_area < 0.03: continue

            sl_s = cv2.resize(rot_d, (nw, nh), interpolation=cv2.INTER_NEAREST)
            if nh <= h_g and nw <= w_g:
                score, _ = match_score(gt_d, sl_s)
            elif nh >= h_g and nw >= w_g:
                score, _ = match_score(sl_s, gt_d)
            else:
                bh = max(h_g, nh); bw = max(w_g, nw)
                pg = np.zeros((bh, bw), np.uint8); ps = np.zeros((bh, bw), np.uint8)
                pg[:h_g, :w_g] = gt_d; ps[:nh, :nw] = sl_s
                score, _ = match_score(pg, ps)
            if score > best_score:
                best_score, best_angle, best_scale = score, angle, scale

    print(f"  Coarse best: angle={best_angle}°  scale={best_scale:.2f}x  NCC={best_score:.4f}")

    print(f"  Fine search (angle step={angle_refine_step}°)...")
    for angle in range(best_angle - 10, best_angle + 11, angle_refine_step):
        angle = angle % 360
        rot_gray = rotate_map(slam_gray, angle)
        rot_occ  = occ_from_gray(rot_gray)
        rot_crop, _ = crop_to_content(rot_occ)
        rot_d = cv2.dilate(rot_crop.astype(np.uint8) * 255, K, iterations=3)
        h_r, w_r = rot_d.shape

        for scale in np.arange(max(0.1, best_scale - 0.3), best_scale + 0.31, 0.01):
            nh = int(h_r * scale); nw = int(w_r * scale)
            if nh < 10 or nw < 10: continue
            if (nh * nw) / gt_area < 0.03: continue
            sl_s = cv2.resize(rot_d, (nw, nh), interpolation=cv2.INTER_NEAREST)
            if nh <= h_g and nw <= w_g:
                score, _ = match_score(gt_d, sl_s)
            elif nh >= h_g and nw >= w_g:
                score, _ = match_score(sl_s, gt_d)
            else:
                bh = max(h_g, nh); bw = max(w_g, nw)
                pg = np.zeros((bh, bw), np.uint8); ps = np.zeros((bh, bw), np.uint8)
                pg[:h_g, :w_g] = gt_d; ps[:nh, :nw] = sl_s
                score, _ = match_score(pg, ps)
            if score > best_score:
                best_score, best_angle, best_scale = score, angle, scale

    print(f"  Fine best:   angle={best_angle}°  scale={best_scale:.2f}x  NCC={best_score:.4f}")

    # Apply best transform
    rot_gray_final = rotate_map(slam_gray, best_angle)
    h_r, w_r = rot_gray_final.shape
    nh = int(h_r * best_scale); nw = int(w_r * best_scale)
    sl_gray_scaled = cv2.resize(rot_gray_final, (nw, nh), interpolation=cv2.INTER_LINEAR)
    sl_occ_scaled  = occ_from_gray(sl_gray_scaled).astype(np.uint8) * 255

    # Tìm translation trên full GT
    gt_full_d = cv2.dilate(gt_occ.astype(np.uint8) * 255, K, iterations=3)
    sl_d_full  = cv2.dilate(sl_occ_scaled, K, iterations=3)

    # Tìm translation dùng image pyramid để tránh local optimum
    def find_translation(big, small):
        """Tìm translation tốt nhất dùng coarse-to-fine pyramid."""
        best_score, best_dx, best_dy = -1.0, 0, 0
        # Coarse: downsample 4x để tìm vùng gần đúng
        for ds in [8, 4, 2, 1]:
            h_b, w_b = big.shape; h_s, w_s = small.shape
            b_ds = cv2.resize(big,   (max(1,w_b//ds), max(1,h_b//ds)), interpolation=cv2.INTER_AREA)
            s_ds = cv2.resize(small, (max(1,w_s//ds), max(1,h_s//ds)), interpolation=cv2.INTER_AREA)
            if b_ds.shape[0] < s_ds.shape[0] or b_ds.shape[1] < s_ds.shape[1]:
                continue
            res = cv2.matchTemplate(b_ds.astype(np.float32),
                                    s_ds.astype(np.float32), cv2.TM_CCOEFF_NORMED)
            score = float(res.max())
            if score > best_score:
                best_score = score
                _, _, _, (lx, ly) = cv2.minMaxLoc(res)
                best_dx, best_dy = lx * ds, ly * ds
        return best_dx, best_dy, best_score

    if nh <= h_gt and nw <= w_gt:
        dx, dy, t_score = find_translation(gt_full_d, sl_d_full)
        print(f"  Translation NCC: {t_score:.4f}")
    else:
        res = cv2.matchTemplate(sl_d_full.astype(np.float32),
                                gt_full_d.astype(np.float32), cv2.TM_CCOEFF_NORMED)
        _, _, _, (lx, ly) = cv2.minMaxLoc(res)
        dx = -lx; dy = -ly

    print(f"  Translation: ({dx}, {dy})")

    # Paste vào canvas GT size
    canvas_occ  = np.zeros((h_gt, w_gt), np.uint8)
    canvas_gray = np.full((h_gt, w_gt), 205, np.uint8)
    ty0, tx0 = dy, dx
    sy0 = max(0, -ty0); sx0 = max(0, -tx0)
    gy0 = max(0,  ty0); gx0 = max(0,  tx0)
    ph  = min(nh - sy0, h_gt - gy0)
    pw  = min(nw - sx0, w_gt - gx0)
    if ph > 0 and pw > 0:
        src = sl_gray_scaled[sy0:sy0+ph, sx0:sx0+pw]
        canvas_gray[gy0:gy0+ph, gx0:gx0+pw] = src
        canvas_occ [gy0:gy0+ph, gx0:gx0+pw] = (src < 150).astype(np.uint8)

    return canvas_occ > 0, canvas_gray


def compute_metrics(pred, gt, pred_gray, gt_gray, thr=5, n=10000):
    inter = (pred & gt).sum(); union = (pred | gt).sum()
    iou   = float(inter) / float(union) if union > 0 else 0.0
    score, _ = sk_ssim(gt_gray, pred_gray, full=True)
    TP = int((pred & gt).sum()); FP = int((pred & ~gt).sum()); FN = int((~pred & gt).sum())
    prec = TP/(TP+FP+1e-9); rec = TP/(TP+FN+1e-9)
    f1   = 2*prec*rec/(prec+rec+1e-9)
    dist_gt   = distance_transform_edt(~gt)
    dist_pred = distance_transform_edt(~pred)
    comp = float((dist_pred[gt]   <= thr).sum()) / max(gt.sum(),   1)
    acc  = float((dist_gt[pred]   <= thr).sum()) / max(pred.sum(), 1)
    f1d  = 2*comp*acc/(comp+acc+1e-9)
    from scipy.spatial import cKDTree
    pp = np.argwhere(pred).astype(np.float32)
    gp = np.argwhere(gt).astype(np.float32)
    if len(pp) > n: pp = pp[np.random.choice(len(pp), n, False)]
    if len(gp) > n: gp = gp[np.random.choice(len(gp), n, False)]
    if len(pp) > 0 and len(gp) > 0:
        chamfer = (cKDTree(gp).query(pp, 1)[0].mean() +
                   cKDTree(pp).query(gp, 1)[0].mean()) / 2
        hd = max(directed_hausdorff(pp, gp)[0], directed_hausdorff(gp, pp)[0])
    else:
        chamfer = hd = float('inf')
    return dict(iou=iou, ssim=float(score),
                precision=prec, recall=rec, f1=f1,
                completeness=comp, accuracy=acc, f1_dist=f1d,
                chamfer=chamfer, hausdorff=hd, TP=TP, FP=FP, FN=FN)


def visualize(gt_occ, pred_occ, gt_gray, pred_gray, out_dir, name, scale=3):
    os.makedirs(out_dir, exist_ok=True)
    h, w = gt_occ.shape

    # --- Crop tight quanh vùng có nội dung (cả GT lẫn SLAM) ---
    both = gt_occ | pred_occ
    rows = np.any(both, axis=1); cols = np.any(both, axis=0)
    pad = 30
    r0 = max(0, np.where(rows)[0][0]  - pad)
    r1 = min(h, np.where(rows)[0][-1] + pad)
    c0 = max(0, np.where(cols)[0][0]  - pad)
    c1 = min(w, np.where(cols)[0][-1] + pad)

    gt_c   = gt_occ  [r0:r1, c0:c1]
    pred_c = pred_occ[r0:r1, c0:c1]

    # --- Overlay: nền trắng, GT=xanh lá, SLAM=xanh dương, TP=trắng ---
    ov = np.full((r1-r0, c1-c0, 3), 245, np.uint8)
    ov[gt_c]              = [0, 160, 0]
    ov[pred_c]            = [0, 0, 200]
    ov[gt_c & pred_c]     = [100, 180, 100]   # vùng khớp = xanh nhạt

    # --- Error map: nền trắng ---
    err = np.full((r1-r0, c1-c0, 3), 245, np.uint8)
    err[gt_c & pred_c]    = [0, 180, 0]    # TP  = xanh lá
    err[gt_c & ~pred_c]   = [0, 0, 220]    # FN  = xanh dương
    err[~gt_c & pred_c]   = [200, 0, 0]    # FP  = đỏ

    # --- Scale to cho dễ nhìn ---
    def upscale(img):
        return cv2.resize(img,
                          (img.shape[1]*scale, img.shape[0]*scale),
                          interpolation=cv2.INTER_NEAREST)

    ov_big  = upscale(ov)
    err_big = upscale(err)

    # Separator dọc
    sep = np.ones((ov_big.shape[0], 20, 3), np.uint8) * 180

    combined = np.hstack([ov_big, sep, err_big])

    # --- Lưu ảnh chính ---
    path = os.path.join(out_dir, f"{name}_comparison.png")
    cv2.imwrite(path, combined)

    # --- Legend ---
    leg_h, leg_w = 175, 420
    leg = np.ones((leg_h, leg_w, 3), np.uint8) * 250
    items = [([0,160,0],   "GT obstacle"),
             ([0,0,200],   "SLAM obstacle"),
             ([100,180,100],"Khớp (TP) — overlay"),
             ([0,180,0],   "TP — error map"),
             ([0,0,220],   "Bỏ sót FN (xanh dương)"),
             ([200,0,0],   "Dư FP (đỏ)")]
    for i, (c, t) in enumerate(items):
        y = 22 + i*27
        cv2.rectangle(leg, (8, y-13), (36, y+9), c, -1)
        cv2.putText(leg, t, (46, y+4), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (30,30,30), 1)
    cv2.imwrite(os.path.join(out_dir, f"{name}_legend.png"), leg)
    print(f"  Saved: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gt',        required=True)
    ap.add_argument('--slam',      required=True)
    ap.add_argument('--output',    default='map_comparison')
    ap.add_argument('--name',      default='result')
    ap.add_argument('--threshold', type=int, default=5)
    ap.add_argument('--angle-step', type=int, default=5)
    ap.add_argument('--angle-min',  type=int, default=0,
                    help='Góc bắt đầu search (default=0°)')
    ap.add_argument('--angle-max',  type=int, default=360,
                    help='Góc kết thúc search (default=360°)')
    ap.add_argument('--no-align',   action='store_true')
    args = ap.parse_args()

    print(f"\n{'='*56}\n  MAP COMPARISON: GT vs SLAM\n{'='*56}")
    gt_gray, gt_occ, _ = load_map(args.gt)
    sl_gray, sl_occ, _ = load_map(args.slam)
    print(f"GT  : {gt_gray.shape[1]}x{gt_gray.shape[0]}px  obs={gt_occ.sum():,}")
    print(f"SLAM: {sl_gray.shape[1]}x{sl_gray.shape[0]}px  obs={sl_occ.sum():,}\n")

    if args.no_align:
        h, w = gt_gray.shape
        sl_occ_a  = cv2.resize(sl_occ.astype(np.uint8)*255, (w, h),
                               interpolation=cv2.INTER_NEAREST) > 0
        sl_gray_a = cv2.resize(sl_gray, (w, h))
    else:
        print(f"[1/2] Aligning (angle_step={args.angle_step}°, range=[{args.angle_min}°,{args.angle_max}°])...")
        sl_occ_a, sl_gray_a = align_maps(sl_gray, gt_gray,
                                         angle_step=args.angle_step,
                                         angle_min=args.angle_min,
                                         angle_max=args.angle_max)

    print(f"\n[2/2] Metrics (threshold={args.threshold}px)...\n")
    m = compute_metrics(sl_occ_a, gt_occ, sl_gray_a, gt_gray, args.threshold)

    S = "─" * 54
    print(f"{'KẾT QUẢ SO SÁNH':^54}\n{S}")
    rows = [("IoU (Jaccard)", m['iou']), ("SSIM", m['ssim']), None,
            ("Precision", m['precision']), ("Recall", m['recall']),
            ("F1 pixel-exact", m['f1']), None,
            (f"Completeness (≤{args.threshold}px)", m['completeness']),
            (f"Map Accuracy (≤{args.threshold}px)", m['accuracy']),
            ("F1 distance-based", m['f1_dist']), None,
            ("Chamfer Distance (px)", m['chamfer']),
            ("Hausdorff Distance (px)", m['hausdorff'])]
    for r in rows:
        if r is None: print(S)
        else: print(f"  {r[0]:<36}{r[1]:>14.4f}")
    print(S)
    print(f"  TP={m['TP']:,}   FP={m['FP']:,}   FN={m['FN']:,}")
    print(S)
    iou, f1d, ss = m['iou'], m['f1_dist'], m['ssim']
    lbl = ("Xuất sắc ✓" if f1d >= 0.90 else
           "Tốt       " if f1d >= 0.75 else
           "Khá       " if f1d >= 0.55 else
           "Kém       ")
    print(f"\n  📊 {lbl}  IoU={iou:.3f}  F1_dist={f1d:.3f}  SSIM={ss:.3f}\n")

    os.makedirs(args.output, exist_ok=True)
    rp = os.path.join(args.output, f"{args.name}_report.txt")
    with open(rp, 'w') as f:
        f.write(f"GT  : {args.gt}\nSLAM: {args.slam}\n\n")
        for k, v in m.items(): f.write(f"{k}: {v}\n")
    print(f"  Report: {rp}")
    visualize(gt_occ, sl_occ_a, gt_gray, sl_gray_a, args.output, args.name)


if __name__ == '__main__':
    main()
