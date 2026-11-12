export default function Privacidade() {
  return (
    <article className="texto">
      <h1>Privacidade e LGPD</h1>
      <p>O ZelaCidade coleta só o necessário para registrar e acompanhar problemas em espaços públicos.</p>

      <h2>O que coletamos e por quê</h2>
      <ul>
        <li><strong>Foto do problema:</strong> para mostrar e classificar o problema. Antes de salvar, a foto é reduzida e perde os metadados (EXIF), que podem conter a posição do aparelho e o modelo do celular.</li>
        <li><strong>Local e descrição:</strong> para pôr o problema no mapa e orientar quem vai resolver.</li>
        <li><strong>E-mail (opcional):</strong> só com o seu consentimento, para enviar avisos sobre a ocorrência. Ele nunca aparece no site e, nos indicadores, vira um código irreversível (hash).</li>
        <li><strong>Identificador aleatório do aparelho:</strong> para contar uma confirmação por pessoa. Guardamos apenas um código derivado dele, que não identifica você.</li>
      </ul>

      <h2>O que fica público</h2>
      <p>Foto, local, descrição, categoria, status e linha do tempo. Por isso, não fotografe rostos, placas de carro nem o interior de casas.</p>

      <h2>Inteligência artificial</h2>
      <p>A IA de visão apenas sugere a categoria e mostra a confiança. Quem confirma é você. A prioridade é definida por regras explicadas na própria ocorrência.</p>

      <h2>Dados simulados</h2>
      <p>Para testar o piloto, parte dos registros é simulada. Eles têm o selo “Simulado” e podem ser escondidos nos filtros.</p>

      <h2>Guarda e exclusão</h2>
      <p>Este é um MVP acadêmico (Global Solution FIAP 2026.2). Os dados ficam guardados só durante o piloto. Para pedir a exclusão de um registro seu, fale com a equipe pelo repositório público do projeto, informando o protocolo.</p>
    </article>
  );
}
