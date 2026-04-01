-- Correção do Security Advisor Supervisor: Habilitar RLS
ALTER TABLE public.systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_system_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employees ENABLE ROW LEVEL SECURITY;

-- ATENÇÃO: Se o seu backend Flask usa a "service_role_key", o sistema 
-- continuará funcionando normalmente pois a chave de serviço ignora o RLS.

-- Políticas sugeridas caso haja consultas vindo diretamente de Frontends 
-- ou clientes usando a chave "anon" / "authenticated":

-- 1. Permite que usuários autenticados (logados) visualizem os sistemas
CREATE POLICY "Sistemas visíveis para usuários autenticados" ON public.systems
    FOR SELECT TO authenticated USING (true);

-- 2. Permite que usuários autenticados visualizem a lista de funcionários (se necessário)
CREATE POLICY "Funcionários visíveis para usuários autenticados" ON public.employees
    FOR SELECT TO authenticated USING (true);

-- 3. Permite que o usuário visualize apenas os acessos que ele mesmo possui
CREATE POLICY "Usuário vê apenas seus próprios acessos" ON public.user_system_access
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
