# 📝 Como Configurar o Arquivo .env

## ❓ Problema: "Não encontrei o .env file pra editar"

**Isso é normal!** O arquivo `.env` **não existe** no repositório por questões de segurança.

### Por que o arquivo .env não está no repositório?

O arquivo `.env` contém informações sensíveis (como sua chave de API da OpenAI) e **nunca** deve ser compartilhado ou commitado no git. Por isso:

- ✅ O arquivo `.env.example` existe (é um template)
- ❌ O arquivo `.env` NÃO existe (você precisa criar)
- 🔒 O arquivo `.env` está no `.gitignore` (não será commitado mesmo se criado)

## 🛠️ Passo a Passo: Como Criar o Arquivo .env

### Passo 1: Copiar o Template

Você precisa copiar o arquivo `.env.example` para criar seu `.env`:

#### No Linux/Mac:
```bash
cp .env.example .env
```

#### No Windows (Prompt de Comando - CMD):
```cmd
copy .env.example .env
```

#### No Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### Manualmente (qualquer sistema):
1. Abra o arquivo `.env.example` com um editor de texto
2. Copie todo o conteúdo
3. Crie um novo arquivo chamado `.env` (sem "example")
4. Cole o conteúdo
5. Salve o arquivo

### Passo 2: Editar o Arquivo .env

Abra o arquivo `.env` (que você acabou de criar) com um editor de texto:
- **Windows:** Notepad, Notepad++, VSCode
- **Linux/Mac:** nano, vim, VSCode, gedit

Encontre a linha:
```
OPENAI_API_KEY=sua-chave-openai-aqui
```

Substitua `sua-chave-openai-aqui` pela sua chave real da OpenAI:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Salve o arquivo!**

### Passo 3: Verificar

Certifique-se de que:
1. ✅ O arquivo `.env` existe na raiz do projeto (mesma pasta do README.md)
2. ✅ O arquivo `.env` contém sua chave OpenAI real
3. ✅ Você salvou as alterações

## 🔍 Verificação Rápida

Para verificar se o arquivo .env foi criado corretamente:

### Linux/Mac:
```bash
# Verificar se o arquivo existe
ls -la .env

# Ver o conteúdo (CUIDADO: não compartilhe a saída!)
cat .env
```

### Windows (CMD):
```cmd
# Verificar se o arquivo existe
dir .env

# Ver o conteúdo (CUIDADO: não compartilhe a saída!)
type .env
```

### Windows (PowerShell):
```powershell
# Verificar se o arquivo existe
Get-Item .env

# Ver o conteúdo (CUIDADO: não compartilhe a saída!)
Get-Content .env
```

## ⚠️ Avisos Importantes

1. **NUNCA** compartilhe seu arquivo `.env` com ninguém
2. **NUNCA** faça commit do arquivo `.env` no git
3. **NUNCA** poste o conteúdo do `.env` em issues, fóruns ou chat
4. A chave da OpenAI é sensível - proteja-a como uma senha

## 🆘 Problemas Comuns

### "Arquivo .env não está sendo lido"
- Verifique se o arquivo está na **raiz do projeto** (mesma pasta que README.md)
- Certifique-se de que o nome é exatamente `.env` (com o ponto no início)
- Reinicie o servidor após criar/modificar o `.env`

### "Erro de API Key mesmo com .env configurado"
1. Abra o arquivo `.env` e verifique se a chave está correta
2. Verifique se não há espaços extras antes ou depois da chave
3. Certifique-se de que a linha não está comentada (não deve começar com `#`)
4. Reinicie o servidor backend

### "No Windows, não consigo ver o arquivo .env"
- No Explorer, habilite "Mostrar arquivos ocultos"
- Ou use o Prompt de Comando/PowerShell para verificar

## 📚 Referências

- [README.md](README.md) - Instruções gerais de instalação
- [ENV_IMPLEMENTATION.md](ENV_IMPLEMENTATION.md) - Detalhes técnicos da implementação
- [.env.example](.env.example) - Template do arquivo de configuração
