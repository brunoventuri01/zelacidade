# Modelo de visão (Applied Computer Vision)

Arquivos entregues pelo Guilherme Alves de Lima (disciplina Applied Computer Vision):

| Arquivo | Conteúdo |
|---|---|
| `best.onnx` | YOLO11n, v1, classe única `buraco`, opset 17, entrada estática |
| `classes.json` | `{"0": "buraco"}` |
| `config.json` | Pré e pós-processamento usados no treino e no `esperado.json` |

**Versão final (v1):** treinada só com o dataset público Pothole (Roboflow, licença ODbL v1.0). No conjunto de teste
(67 imagens, 177 buracos): mAP50 de 0,793 e, no limiar de 0,35 que o MVP usa, precisão de 0,79 e recall de 0,68.
Não haverá v2. Se o modelo for trocado um dia, atualize também `backend/tests/visao/esperado.json`.

## Contrato usado pelo backend (`app/visao.py`)

- Entrada `images`, float32 `[1, 3, 640, 640]`, NCHW, RGB ÷255.
- Letterbox centralizado: ganho = min(640/h, 640/w), cor da borda 114. O redimensionamento reproduz o
  `cv2.INTER_LINEAR` bit a bit, sem depender do OpenCV.
- Saída `output0`, float32 `[1, 5, 8400]`, sem NMS: linhas 0–3 = cx, cy, w, h em pixels do quadro 640; linha 4 =
  score já com sigmoid.
- Pós-processamento: confiança ≥ 0,35 (`CV_CONF_LIMIAR`), NMS com IoU 0,7. Para desfazer o letterbox,
  x = (x − borda_x) / ganho e y = (y − borda_y) / ganho, recortando aos limites da imagem.
- Severidade (regra do Guilherme), com a área relativa à imagem original: 0 caixas → nenhuma; maior área ≥ 0,05 ou
  ≥ 4 caixas → alta; maior área ≥ 0,015 ou ≥ 2 caixas → média; senão baixa.

O teste `backend/tests/test_visao_modelo.py` confere que o backend reproduz as 5 saídas do `esperado.json`
(contagem, severidade, notas com tolerância de 0,002 e caixas com tolerância de 0,5 px). O `esperado.json` é o que
o modelo responde, não um gabarito: a `teste_4` sai sem caixas e cobre o caminho "nenhuma detecção".

Sem o `best.onnx`, o MVP continua funcionando: a tela de registro avisa que a análise automática está
indisponível e o morador escolhe a categoria.
