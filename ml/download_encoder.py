"""Download fixed pretrained feature extractor once; no external inference service."""
from sentence_transformers import SentenceTransformer
from ml.model import ENCODER, ENCODER_REVISION
if __name__ == '__main__':
    SentenceTransformer(ENCODER,revision=ENCODER_REVISION)
    print('Multilingual encoder cached for offline training and inference.')
