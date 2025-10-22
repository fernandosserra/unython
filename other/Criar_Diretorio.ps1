# Protocolo de Implantação de Estrutura V2.0 - Ajuste Dimensional
# --------------------------------------------------------------------------------------------------
# É claro que eu sei o seu caminho. A Washu nunca erra um alvo!
$BaseDir = "C:\Unython"

# Define a estrutura de pastas hierárquicas. 
# A ordem é crucial para que a pasta pai exista antes da filha!
$Directories = @(
    "app",
    "assets",
    "assets\img",
    "assets\sound",
    "data",
    "docs",
    "other", # O refúgio para os scripts de implantação!
    "src",
    "src\modules", # Onde ficarão os Services (Agendamento, Vendas)
    "src\utils",  # Onde ficarão os Models (Entidades)
    "tests"
)

Write-Host "Iniciando a recalibração da Estrutura de Diretórios V2.0 por Washu Hakubi..."

# 1. Criação dos Diretórios (Garantindo a Ordem Universal)
Set-Location -Path $BaseDir
foreach ($Dir in $Directories) {
    $NewPath = Join-Path -Path $BaseDir -ChildPath $Dir
    New-Item -Path $NewPath -ItemType Directory -Force | Out-Null
    Write-Host " -> Estrutura Dimensional: '$Dir' criada."
}

# 2. Criação dos Arquivos de Inicialização (Estabelecendo a Lógica Elemental)

# Lista dos arquivos a serem criados (para que o Python entenda a modularidade)
$FilesToCreate = @(
    # Torna 'src' um pacote
    "src\__init__.py", 
    # Torna 'modules' um pacote
    "src\modules\__init__.py", 
    # Torna 'utils' um pacote (Onde Models e DatabaseManager ficarão)
    "src\utils\__init__.py"
)

foreach ($File in $FilesToCreate) {
    $NewFilePath = Join-Path -Path $BaseDir -ChildPath $File
    New-Item -Path $NewFilePath -ItemType File -Force | Out-Null
    Write-Host " -> Artefato Lógico: '$File' criado."
}

# 3. Movendo o script atual para a pasta 'other' (Isolamento do Artefato)
$CurrentScriptPath = Join-Path -Path $BaseDir -ChildPath "Criar_Diretorio.ps1"
$DestinationPath = Join-Path -Path $BaseDir -ChildPath "other\Criar_Diretorio.ps1"

if (Test-Path $CurrentScriptPath) {
    Move-Item -Path $CurrentScriptPath -Destination $DestinationPath -Force | Out-Null
    Write-Host " -> Script de Gênia movido para 'other'. Limpando o Espaço-Tempo."
}

Write-Host "--------------------------------------------------------------------------------------------------"
Write-Host "Sua Estrutura de Projeto Unython está perfeitamente calibrada! Ordem total estabelecida."