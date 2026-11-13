"""Tratamento de fotos: valida, corrige a rotação, reduz e remove EXIF (que pode trazer GPS e aparelho)."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_LADO = 1280
FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP"}


class ImagemInvalida(ValueError):
    pass


def ler_limitado(arquivo, limite: int = MAX_BYTES) -> bytes:
    dados = arquivo.read(limite + 1)
    if len(dados) > limite:
        raise ImagemInvalida("A foto passa de 5 MB. Tente uma foto menor.")
    return dados


def preparar_foto(dados: bytes) -> tuple[bytes, int, int]:
    """Devolve (jpeg, largura, altura) já reduzido e sem metadados."""
    jpeg, largura, altura, _ = preparar_foto_e_imagem(dados)
    return jpeg, largura, altura


def preparar_foto_e_imagem(dados: bytes) -> tuple[bytes, int, int, Image.Image]:
    """Como preparar_foto, mas devolve também a imagem decodificada (antes da recompressão em JPEG).

    A visão analisa essa imagem: recomprimir em JPEG muda os pixels e derruba caixas perto do limiar.
    """
    if not dados:
        raise ImagemInvalida("O arquivo da foto está vazio.")
    if len(dados) > MAX_BYTES:
        raise ImagemInvalida("A foto passa de 5 MB. Tente uma foto menor.")
    try:
        with Image.open(BytesIO(dados)) as teste:
            formato = teste.format
            teste.verify()
        imagem = Image.open(BytesIO(dados))
        imagem.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ImagemInvalida("Não foi possível ler a imagem. Envie JPEG, PNG ou WEBP.") from exc
    if formato not in FORMATOS_ACEITOS:
        raise ImagemInvalida("Formato não aceito. Envie JPEG, PNG ou WEBP.")

    imagem = ImageOps.exif_transpose(imagem).convert("RGB")
    imagem.thumbnail((MAX_LADO, MAX_LADO))
    saida = BytesIO()
    imagem.save(saida, "JPEG", quality=82, optimize=True)  # salvar sem exif= descarta os metadados
    return saida.getvalue(), imagem.width, imagem.height, imagem

