from rapidocr import RapidOCR

_engine = RapidOCR()


def run_ocr(img_np):
    output = _engine(img_np)
    if output.boxes is None or output.txts is None or output.scores is None:
        return [], float(output.elapse)
    result = [
        [box.tolist(), text, float(score)]
        for box, text, score in zip(output.boxes, output.txts, output.scores)
    ]
    return result, float(output.elapse)
