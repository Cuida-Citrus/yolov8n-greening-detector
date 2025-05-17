# YOLOv8n Greening Detector

## Descrição
Repositório contendo uma prova de conceito (POC) para detecção de sintomas de **Greening (Huanglongbing)** em folhas de citros, usando o modelo **YOLOv8n**. O objetivo é demonstrar, em ambiente acadêmico, todo o fluxo de treinamento e inferência.

## Contexto Acadêmico
⚠️ **POC para uso estritamente acadêmico**, não se destina a produção ou uso comercial.

## Recursos Disponibilizados
- **Modelo treinado** (YOLOv8n): https://huggingface.co/cuidacitrus/yolov8n-greening-detector
- **Dataset de treinamento/validação**: https://huggingface.co/datasets/cuidacitrus/folhas_greening_e_saudaveis
- **Código de treinamento** (exemplo): pasta `Treinamento/`
- **Notebook de inferência**: pasta `Inferencia/`

## Estrutura do Repositório
```bash
├── Treinamento/          # Scripts e notebooks para treinar o modelo (exemplo)
├── Inferencia/           # Notebook para rodar serviço de inferência\
├── Dashboard/            # Dashboard criado com Power BI
├── terraform/            # Arquivos Terraform (Blob Storage e Cosmos DB)
└── README.md             # Este documento
```

## Pré-requisitos
- Python 3.8 ou superior
- Azure CLI e/ou Terraform (para provisionamento opcional)
- Power BI Desktop ou Power BI Service

## Provisionamento de Infraestrutura
Você pode criar os recursos no **Portal Azure** manualmente ou usar **Terraform**:
1. **Azure Blob Storage**: armazenar imagens de entrada
2. **Azure Cosmos DB** (API Core/SQL): armazenar resultados de inferência

Para usar o Terraform:
```bash
cd terraform
terraform init
terraform apply
```

## Instalação e Setup
```bash
git clone https://github.com/Cuida-Citrus/yolov8n-greening-detector.git
cd yolov8n-greening-detector
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

## Uso

### 1. Treinamento (opcional)
Se desejar treinar localmente (apenas como exemplo):
```bash
jupyter notebook Treinamento/train.ipynb
```
> O modelo pré-treinado já está disponível no Hugging Face, então este passo é opcional.

### 2. Inferência
Execute o notebook de inferência:
```bash
jupyter notebook Inferencia/inferencia.ipynb
```
- Lê imagens do Blob Storage
- Carrega o modelo (local ou do Hugging Face)
- Executa detecção e salva resultados no Cosmos DB

### 3. Visualização no Power BI
1. Abra o Power BI Desktop
2. Conecte-se ao **Azure Cosmos DB** criado
3. Importe a coleção de resultados
4. Utilize os relatórios prontos ou crie visuais para analisar as detecções

## Contribuição
1. Fork este repositório
2. Crie uma branch para sua feature: `git checkout -b feature/nova-funcionalidade`
3. Faça commit das alterações: `git commit -m "Adiciona ..."`
4. Envie para o seu fork: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## Licença
Este repositório é disponibilizado apenas para fins acadêmicos. Todos os direitos sobre modelos e imagens originais pertencem aos autores e instituições responsáveis pelas coletas de dados.
