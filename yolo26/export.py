from ultralytics import YOLO


def main():
    model = YOLO("yolo26s.pt")
    output = model.export(format="onnx", imgsz=640)
    print(f"Exported ONNX model to: {output}")


if __name__ == "__main__":
    main()
