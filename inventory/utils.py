import re
from io import BytesIO
import qrcode
import qrcode.image.svg


def get_qr_code_buffer(full_url: str) -> BytesIO:
    qr_buffer = BytesIO()
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(full_url)
    qr_image = qr.make_image(
        image_factory=factory,
        module_drawer=qrcode.image.styles.moduledrawers.svg.SvgPathCircleDrawer(),
    )
    qr_image.save(qr_buffer)

    return qr_buffer


def generate_location_svg(location: str, prefix: str) -> str:
    """
    Generates an SVG representation of the box location if it matches the given prefix-i-j-k pattern.
    """
    match = re.match(rf"{prefix}-(\d+)-(\d+)-(\d+)", location)
    if not match:
        return ""

    shelf, compartment, pos = map(int, match.groups())

    svg_width = 700
    svg_height = 250
    rack_h = 250
    rack_w = 112
    shelf_w = rack_w
    shelf_h = 5
    box_w = (shelf_w - 9) // 3
    box_h = 35
    min_y = 0
    svg = [
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">',
        "<style> .ivar { stroke: #293133; } .shelf { stroke-width:3; } .frame { stroke-width:6; fill:none } </style>",
    ]
    ys = [0, 30, 80, 140, 200]

    for s in range(1, 5):
        x = 10 + (s - 1) * (shelf_w + 10)
        svg.append(
            f'<line x1="{x}" y1="{min_y}" x2="{x}" y2="{min_y + rack_h}" class="ivar frame"/>'
        )
        svg.append(
            f'<line x1="{x + rack_w}" y1="{min_y}" x2="{x + rack_w}" y2="{min_y + rack_h}" class="ivar frame"/>'
        )
        for c in range(1, 6):
            y = ys[c - 1]
            svg.append(
                f'<rect x="{x}" y="{y}" width="{shelf_w}" height="{shelf_h}" class="ivar shelf"/>'
            )

    for s in range(1, 5):
        x = 10 + (s - 1) * (shelf_w + 10)
        for c in range(1, 5):
            y = (c - 1) * (shelf_h + box_h) + 30
            for b in range(1, 4):
                bx = x + (b - 1) * box_w + b * (shelf_w - box_w * 3) // 3
                this_box_h = box_h if c > 1 else box_h // 2
                by = ys[c] - this_box_h
                stroke = (
                    "#E00909"
                    if (s == shelf and c == compartment and b == pos)
                    else "#785624"
                )
                stroke_width = (
                    "4" if (s == shelf and c == compartment and b == pos) else "2"
                )

                svg.append(
                    f'<rect x="{bx}" y="{by}" width="{box_w - 4}" height="{this_box_h}" fill="#d0b080" stroke="{stroke}" stroke-width="{stroke_width}"/>'
                )
    svg.append("</svg>")
    return "".join(svg)
