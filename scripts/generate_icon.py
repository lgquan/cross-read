from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 10, 246, 246), radius=58, fill=(0, 122, 255, 255))
    draw.rounded_rectangle((54, 55, 202, 205), radius=24, fill=(255, 255, 255, 250))
    draw.line((128, 55, 128, 205), fill=(0, 122, 255, 255), width=10)
    draw.line((78, 92, 108, 92), fill=(0, 122, 255, 255), width=9)
    draw.line((78, 122, 108, 122), fill=(0, 122, 255, 255), width=9)
    draw.line((148, 92, 178, 92), fill=(0, 122, 255, 255), width=9)
    draw.line((148, 122, 178, 122), fill=(0, 122, 255, 255), width=9)

    output = Path(__file__).resolve().parents[1] / "assets" / "cross-read.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        output,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
