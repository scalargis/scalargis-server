from PIL import Image

def get_image_size(filepath):
    img = Image.open(filepath)

    return img.size


def get_extent_from_wordfile(filepath, width, height):
    extent = None

    with open(filepath, 'r') as wld_file:
        lines = wld_file.readlines()
        if len(lines) >= 5:
            pixel_size = float(lines[0].rstrip('\r\n'))
            left_x = float(lines[4].rstrip('\r\n')) - (pixel_size/2)
            top_y = float(lines[5].rstrip('\r\n')) + (pixel_size/2)

        extent = [left_x, top_y - (height * pixel_size), left_x + (width * pixel_size), top_y]

    return extent


def get_extent_from_geotiff(filepath):
    import rasterio
    dataset = rasterio.open(filepath, 'r')
    extent = [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top]

    return extent