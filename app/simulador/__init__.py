"""Núcleo do simulador de carteiras — Python puro, independente de Flask/Django.

Pensado para ser levado ao SaaS da Hadar: basta importar estes módulos e
alimentar ``calculos.simular`` com as operações, cotações, proventos e CDI.

    fontes    -> YahooFinance, BancoCentral (CDI) e Demonstracao (offline)
    regras    -> Movimento, validações de quantidade e de cronologia das vendas
    calculos  -> simular(): posições, rentabilidade (cotas), CDI, espelho CDI, risco, meses
"""
