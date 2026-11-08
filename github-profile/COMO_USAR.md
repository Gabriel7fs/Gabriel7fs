# Perfil dinâmico de Gabriel Furquim

O cartão segue o visual escuro e azul da proposta anterior e busca informações reais do perfil Gabriel7fs. O pacote já inclui uma primeira versão gerada com os dados públicos disponíveis no momento da criação.

## Instalação

1. Extraia o ZIP.
2. Copie o conteúdo de `github-profile/` para a raiz do repositório de perfil `Gabriel7fs/Gabriel7fs`, preservando as pastas. O `README.md` incluído é uma proposta completa para substituir o atual; você também pode aproveitar apenas o cabeçalho.
3. Inclua `.github/workflows/update-profile.yml`. Essa pasta pode ficar oculta no explorador de arquivos. Pelo site do GitHub, você pode criar o arquivo com **Add file → Create new file** e informar o caminho completo.
4. Faça o commit na branch padrão do repositório.
5. Acesse **Actions → Update profile card → Run workflow**. A atualização também é acionada quando você altera `profile.json`, o script, o modelo do cartão ou o workflow.

O agendamento solicita uma atualização diária às 06h23 no horário de Brasília. A execução pode sofrer atraso na fila do GitHub. O agendamento só funciona na branch padrão. O workflow usa o `GITHUB_TOKEN` fornecido pelo GitHub e a permissão `contents: write` para salvar os arquivos gerados; não é necessário criar um token pessoal.

Se uma política do repositório ou da organização impedir o bot de enviar commits, o erro aparecerá no job **Save updated profile**. As regras da branch precisam permitir essa atualização. Se Actions estiver desativado no repositório, ative-o para executar o workflow.

## O que se atualiza automaticamente

- Quantidade de repositórios públicos do perfil, incluindo forks.
- Estrelas recebidas nos repositórios públicos originais, sem forks.
- Seguidores.
- Linguagens por quantidade de bytes nos repositórios públicos originais, sem forks e sem o próprio repositório de perfil. As três principais aparecem individualmente; as demais são agrupadas em `Other`.
- Data e horário da última coleta bem-sucedida.

Essas estatísticas descrevem o perfil público do GitHub. Elas não incluem trabalho privado ou medem tempo de experiência profissional. O gráfico contabiliza bytes presentes nos repositórios, inclusive código de outras pessoas que esses projetos contenham, conforme a API de linguagens do GitHub.

## Experiências, tecnologias e estudos

Edite `profile.json`. As áreas e tecnologias iniciais foram organizadas a partir do README original: HTML5, CSS3, TypeScript, C, Angular, Ionic, Git, GitHub, MySQL, PostgreSQL, Visual Studio Code e Arduino IDE. Java, Spring Boot, Dart e Flutter continuam na seção de estudos.

- `experience`: áreas e descrições exibidas na tabela **Skills & experience**. Você pode trocar essas entradas por experiências profissionais que queira publicar, incluindo empresa, cargo e período.
- `featured_stack` e `featured_learning`: destaques curtos do cartão. Mantenha os textos curtos para preservar a composição.
- `technologies`, `tools`, `databases`, `environments` e `learning`: grupos de badges no README.
- `display_name`, `headline`, `summary` e `detail`: apresentação do cabeçalho. Para textos muito maiores, ajuste o modelo em `templates/profile-card.svg`.
- `language_excluded_repositories`: nomes de outros repositórios que você deseja excluir apenas do cálculo de linguagens.

As experiências profissionais não são deduzidas dos números do GitHub. Os textos são mantidos por você em `profile.json` e aplicados à apresentação na próxima execução. Edite fora dos marcadores `PROFILE-CONTENT` para incluir conteúdo manual no README; dentro deles, o conteúdo é regenerado.

## Arquivos

- `README.md`: perfil completo, com o cartão e as seções de tecnologias.
- `profile.json`: informações editáveis sobre você.
- `.github/workflows/update-profile.yml`: atualização automática.
- `scripts/update_profile.py`: coleta de dados e geração do SVG, usando apenas a biblioteca padrão do Python 3.10 ou superior.
- `templates/profile-card.svg`: modelo visual do cartão.
- `assets/profile-card.svg`: cartão gerado usado pelo README.
- `assets/github-data.json`: última coleta pública concluída, útil para conferir os números.

## Execução local

Na raiz do projeto, execute `python3 scripts/update_profile.py`. Para evitar o limite menor da API sem autenticação, você pode definir `GH_TOKEN` no ambiente local. Não coloque tokens nos arquivos do projeto.

Para apenas renderizar os dados já coletados, execute `python3 scripts/update_profile.py --from-snapshot assets/github-data.json`.

Se uma consulta à API falhar, o processo encerra com erro antes de escrever novos arquivos. O workflow não publica o resultado de uma coleta incompleta; o último cartão permanece disponível. Os números refletem a última execução concluída, e não uma consulta a cada visita. O GitHub também pode manter a imagem em cache por algum tempo.

## Referências

- Repositórios públicos: https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user
- Bytes por linguagem: https://docs.github.com/en/rest/repos/repos#list-repository-languages
- Eventos e agendamentos: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
