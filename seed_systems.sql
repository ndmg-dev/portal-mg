INSERT INTO public.systems (id, name, description, category, url, icon_class, is_public) 
VALUES 
  ('portal-colaborador', 'Portal do Colaborador', 'Gerencie suas informações...', 'main', 'https://portalcolabmg.lovable.app/login', 'icon-portal.png', true),
  ('sistema-comissao', 'Sistema de Cálculo de Comissão', 'Calcule suas comissões...', 'main', 'https://calculadp.lovable.app/', 'icon-comissao.png', false),
  ('ponto-eletronico', 'Processamento Ponto', 'Faça upload dos espelhos...', 'automation', 'https://ai.studio/apps/drive/1g4DXIeeEt42F_J29UEPp15DgEww1PkuM?fullscreenApplet=true', 'icon-ponto.png', false),
  ('adiantamento-salarial', 'Cálculo Adiantamento', 'Importe o PDF...', 'automation', 'https://ai.studio/apps/drive/14NzWtRjoDQhHhwxaDIeZisxTAzIZDkvq?fullscreenApplet=true', 'icon-adiantamento.png', false),
  ('grid-x', 'GridX', 'Seu conversor inteligente para Windows...', 'main', 'https://gridx.lovable.app/', 'icon-gridx.png', true),
  ('arca-mg', 'Arca MG', 'Analisador de Documentos...', 'main', 'https://arcamg.lovable.app/', 'icon-arca.png', true),
  ('aeronord-convocacoes', 'Aeronord - Convocações & Recibos', 'Sistema interno para cálculo automático de convocações...', 'main', 'https://nordcv.lovable.app/cv', 'icon-aeronord.png', true),
  ('calculadora-rescisao', 'Calculadora de Rescisão', 'Ferramenta automática para cálculo de rescisão trabalhista...', 'main', 'https://calculadoramg.lovable.app/', 'icon-rescisao.png', true)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  url = EXCLUDED.url,
  category = EXCLUDED.category,
  icon_class = EXCLUDED.icon_class,
  is_public = EXCLUDED.is_public;
