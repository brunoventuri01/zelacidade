# Modelo de visão (Applied Computer Vision)

Coloque aqui os arquivos entregues pelo Guilherme:

- `best.onnx`: YOLO11n treinado para a classe `buraco`, entrada 640×640.
- `classes.json`: `{"0": "buraco"}`.

Contrato usado pelo backend (`app/visao.py`):

- pré-processamento: letterbox 640 com borda cinza 114, RGB, valores ÷255, NCHW float32;
- saída aceita: bruta `[1, 5, 8400]` (cx, cy, w, h, score), com NMS feito no backend, ou com NMS embutido `[1, K, 6]`;
- limiar de confiança: variável `CV_CONF_LIMIAR` (padrão 0,35).

Sem o `best.onnx`, o MVP funciona normalmente: a tela de registro avisa que a análise automática está
indisponível e o morador escolhe a categoria.
