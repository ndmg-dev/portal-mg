-- Migration Script for Supabase (PostgreSQL)

-- 1. Systems Table
CREATE TABLE IF NOT EXISTS public.systems (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'main',
    url TEXT NOT NULL,
    icon_class TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Profiles Table (Extends Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on Profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. User System Access Table (RBAC)
CREATE TABLE IF NOT EXISTS public.user_system_access (
    user_id UUID REFERENCES auth.users ON DELETE CASCADE,
    system_id TEXT REFERENCES public.systems ON DELETE CASCADE,
    granted_by UUID REFERENCES auth.users,
    granted_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, system_id)
);

-- 4. Audit Logs Table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id UUID REFERENCES auth.users,
    target_id TEXT,
    action TEXT NOT NULL,
    meta_info JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Employees Table (Official List)
CREATE TABLE IF NOT EXISTS public.employees (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Policies for Profiles
CREATE POLICY "Public profiles are viewable by everyone." ON public.profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own profiles." ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, role)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name', 'user');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
