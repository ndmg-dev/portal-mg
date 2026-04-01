INSERT INTO public.systems (id, name, description, category, url, icon_class, is_public) 
VALUES 
  -- Aqueles dois do portal antigo que usavam arquivos .png hospedados
  ('abertura-empresa', 'Abertura de Empresa', 'Acompanhamento e viabilidade para esteira de constituição de novas empresas.', 'main', 'https://abertura.mendoncagalvao.com.br', 'abertura_empresa.png', true),
  ('central-suporte', 'Central de Suporte', 'Abertura e acompanhamento de chamados técnicos para o time interno.', 'main', 'https://suporte.mendoncagalvao.com.br', 'central_suporte.png', true),
  
  -- Os 4 sistemas inéditos USING FONTAWESOME CLASSES DYNAMICALLY
  ('ouvidoria-rh', 'Ouvidoria Interna (RH)', 'Canal seguro, transparente e confidencial para resolução de conflitos, sugestões e reportes voltados ao Recursos Humanos.', 'main', 'https://ouvidoria.mendoncagalvao.com.br', 'fa-solid fa-user-shield', true),
  
  ('contai', 'ContAI', 'Robô de Inteligência Artificial nativo, focado em ler, processar e realizar a conciliação automática de extratos bancários complexos.', 'automation', 'https://contai.mendoncagalvao.com.br', 'fa-solid fa-microchip', true),
  
  ('bimg', 'BIMG - Business Intelligence', 'Painéis avançados de visualização de dados aplicados às consultorias financeiras e societárias (Exclusivo Consultores).', 'automation', 'https://bimg.nucleodigital.cloud', 'fa-solid fa-chart-pie', false),
  
  ('gestor-ferias', 'Agendamento de Férias', 'Módulo gerencial exclusivo para coordenadores de setores coordenarem escalas e solicitações de férias dos colaboradores.', 'main', 'https://ferias.nucleodigital.cloud', 'fa-solid fa-umbrella-beach', false)

ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  url = EXCLUDED.url,
  category = EXCLUDED.category,
  icon_class = EXCLUDED.icon_class,
  is_public = EXCLUDED.is_public;
