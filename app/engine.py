from rapidocr_onnxruntime import RapidOCR

_engine = RapidOCR()


def run_ocr(img_np):
    result, elapse = _engine(img_np)
    return result, _elapse_to_seconds(elapse)


def _elapse_to_seconds(elapse) -> float:
    if elapse is None:
        return 0.0
    if isinstance(elapse, (list, tuple)):
        return float(sum(e for e in elapse if e is not None))
    return float(elapse)
