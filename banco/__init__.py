from .sicoob import process as process_sicoob
from .itau import process as process_itau
from .caixa import process as process_caixa
from .inter import process as process_inter
from .nubank import process as process_nubank
from .bradesco import process as process_bradesco
from .itau2 import process as process_itau2
from .itau3 import process as process_itau3
from .santander import process as process_santander
from .sicredi import process as process_sicredi
from .pagbank import process as process_pagbank

BANK_PROCESSORS = {
    "Sicoob": process_sicoob,
    "Itaú": process_itau,
    "Caixa": process_caixa,
    "Banco Inter": process_inter,
    "Nubank": process_nubank,
    "Bradesco": process_bradesco,
    "Itaú2": process_itau2,
    "Itaú3": process_itau3,
    "Santander": process_santander,
    "Sicredi": process_sicredi,
    "PagBank": process_pagbank
}

def get_processor(bank):
    processor = BANK_PROCESSORS.get(bank)
    if not processor:
        raise ValueError(f"Banco não suportado: {bank}")
    return processor