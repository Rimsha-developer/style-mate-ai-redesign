
import numpy as np


def _pad_to_square(arr, fill=(220, 220, 220)):
    """Pad a crop to a square canvas with neutral background, preserving aspect ratio.

    This is critical: the CNN was trained on 224×224 images.  When a body-region
    crop is very narrow (e.g. 182×931, aspect ratio 0.20) and is simply resized to
    224×224 it gets squashed so severely that the network cannot recognise the
    garment type. Letterboxing fixes this by keeping the garment's proportions
    intact before the resize step in engine._prep().
    """
    h, w = arr.shape[:2]
    side = max(h, w)
    canvas = np.full((side, side, 3), fill, dtype=np.uint8)
    y_off = (side - h) // 2
    x_off = (side - w) // 2
    canvas[y_off:y_off + h, x_off:x_off + w] = arr
    return canvas


def get_box(points, width, height, padding=0.3):
    """Return (x1, y1, x2, y2) bounding box for the given landmark points.

    Padding is expressed as a fraction of the bounding-box span on each axis.
    We use a reduced default of 0.3 (was 0.5) to avoid over-extending the lower
    crop into the shoes/feet region, which previously caused the lower crop to
    contain mostly feet and background, leading to wrong predictions like Heels.
    """
    xs = [p.x * width for p in points]
    ys = [p.y * height for p in points]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    pad_x = (x_max - x_min) * padding
    pad_y = (y_max - y_min) * padding

    x1 = max(0, int(x_min - pad_x))
    x2 = min(width, int(x_max + pad_x))
    y1 = max(0, int(y_min - pad_y))
    y2 = min(height, int(y_max + pad_y))

    return x1, y1, x2, y2


def crop_garments(image, landmarks):
    """Extract upper and lower garment regions from a full-body image.

    Returns:
        (upper_crop, lower_crop) — both letterboxed to square so that
        engine._prep() can resize to 224×224 without distorting proportions.

    Landmark indices used (MediaPipe Pose):
        11, 12 – left/right shoulder
        23, 24 – left/right hip
        27, 28 – left/right ankle
    """
    height, width = image.shape[:2]

    shoulders = [landmarks[11], landmarks[12]]
    hips = [landmarks[23], landmarks[24]]
    ankles = [landmarks[27], landmarks[28]]

    # Upper garment: shoulder → hip region (torso)
    upper_box = get_box(shoulders + hips, width, height, padding=0.3)

    # Lower garment: hip → ankle region (legs).
    # We use reduced X-padding (0.3) to avoid including background on both sides
    # and cap the bottom at ~90 % of the ankle Y position to exclude feet/shoes.
    lx1, ly1, lx2, ly2 = get_box(hips + ankles, width, height, padding=0.3)
    ankle_y = int(np.mean([lm.y * height for lm in ankles]))
    knee_y = int(np.mean([lm.y * height for lm in hips]) +
                 (ankle_y - np.mean([lm.y * height for lm in hips])) * 0.85)
    ly2 = min(ly2, knee_y)         # exclude feet – cut off near knee level (85 % of hip→ankle)
    lower_box = (lx1, ly1, lx2, ly2)

    ux1, uy1, ux2, uy2 = upper_box
    lx1, ly1, lx2, ly2 = lower_box

    upper_crop = image[uy1:uy2, ux1:ux2]
    lower_crop = image[ly1:ly2, lx1:lx2]

    if upper_crop.size == 0 or lower_crop.size == 0:
        raise ValueError("Invalid garment crop: one or both regions are empty")

    # Letterbox both crops to square so CNN receives properly proportioned input
    upper_sq = _pad_to_square(upper_crop)
    lower_sq = _pad_to_square(lower_crop)

    return upper_sq, lower_sq
