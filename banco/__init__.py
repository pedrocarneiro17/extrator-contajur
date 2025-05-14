from .sicoob import process as process_sicoob
from .itau import process as process_itau
from .caixa import process as process_caixa
from .inter import process as process_inter
from .nubank import process as process_nubank

BANK_PROCESSORS = {
    "Sicoob": process_sicoob,
    "Itaú": process_itau,
    "Caixa": process_caixa,
    "Inter": process_inter,
    "Nubank": process_nubank,
}

def get_processor(bank):
    processor = BANK_PROCESSORS.get(bank)
    if not processor:
        raise ValueError(f"Banco não suportado: {bank}")
    return processor