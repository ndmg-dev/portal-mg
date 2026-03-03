"""
brevo_mail.py
=============
Módulo responsável pelo envio de e-mails via Brevo API.
Utilizado para recuperação de senha com template HTML customizado.
"""

import os
import requests

BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
SENDER_EMAIL = "nucleodigitalmendoncagalvao@gmail.com"
SENDER_NAME = "Núcleo Digital MG"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Envia e-mail de recuperação de senha via Brevo API.

    Args:
        to_email: E-mail do destinatário.
        reset_link: Link completo para redefinição de senha.

    Returns:
        True se enviado com sucesso, False em caso de erro.
    """
    if not BREVO_API_KEY:
        print("[ERROR] BREVO_API_KEY não configurada no .env")
        return False

    html_body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Redefinição de Senha</title>
</head>
<body style="margin:0;padding:0;background-color:#0f0f0f;font-family:'Inter',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f0f0f;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background-color:#1a1a1a;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">

          <!-- Cabeçalho dourado -->
          <tr>
            <td style="background:linear-gradient(135deg,#fbbf24,#f59e0b);padding:6px 0;"></td>
          </tr>

          <!-- Logo e título -->
          <tr>
            <td align="center" style="padding:40px 40px 24px;">
              <p style="margin:0 0 16px;font-size:13px;font-weight:600;letter-spacing:2px;color:#fbbf24;text-transform:uppercase;">Mendonça Galvão Contadores Associados</p>
              <h1 style="margin:0;font-size:22px;font-weight:700;color:#ffffff;">Redefinição de Senha</h1>
            </td>
          </tr>

          <!-- Corpo -->
          <tr>
            <td style="padding:0 40px 32px;">
              <p style="margin:0 0 16px;font-size:15px;color:#9ca3af;line-height:1.6;">
                Recebemos uma solicitação para redefinir a senha da sua conta na
                <strong style="color:#e5e7eb;">Central de Sistemas MG</strong>.
              </p>
              <p style="margin:0 0 32px;font-size:15px;color:#9ca3af;line-height:1.6;">
                Clique no botão abaixo para criar uma nova senha. O link é válido por <strong style="color:#e5e7eb;">1 hora</strong>.
              </p>

              <!-- Botão CTA -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="{reset_link}"
                       style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#1a1a1a;font-size:15px;font-weight:700;text-decoration:none;border-radius:8px;letter-spacing:0.3px;">
                      Redefinir Minha Senha
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Link alternativo -->
              <p style="margin:28px 0 0;font-size:12px;color:#6b7280;line-height:1.6;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </p>
              <p style="margin:6px 0 0;font-size:12px;word-break:break-all;">
                <a href="{reset_link}" style="color:#fbbf24;text-decoration:none;">{reset_link}</a>
              </p>

              <!-- Aviso -->
              <div style="margin:28px 0 0;padding:16px;background:rgba(251,191,36,0.06);border-left:3px solid #fbbf24;border-radius:4px;">
                <p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.5;">
                  ⚠️ Se você não solicitou a redefinição de senha, ignore este e-mail. Sua senha permanece a mesma.
                </p>
              </div>
            </td>
          </tr>

          <!-- Rodapé -->
          <tr>
            <td style="padding:24px 40px;border-top:1px solid rgba(255,255,255,0.06);">
              <p style="margin:0;font-size:12px;color:#4b5563;text-align:center;line-height:1.6;">
                Este é um e-mail automático enviado pelo sistema da<br>
                <strong style="color:#6b7280;">Mendonça Galvão Contadores Associados</strong><br>
                Não responda a este e-mail.
              </p>
            </td>
          </tr>

          <!-- Barra inferior dourada -->
          <tr>
            <td style="background:linear-gradient(135deg,#fbbf24,#f59e0b);padding:4px 0;"></td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Redefinição de Senha — Central de Sistemas MG",
        "htmlContent": html_body,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            print(f"[INFO] E-mail de reset enviado para {to_email}")
            return True
        else:
            print(f"[ERROR] Brevo API retornou {response.status_code}: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout ao conectar com a API do Brevo")
        return False
    except Exception as e:
        print(f"[ERROR] Falha ao enviar e-mail via Brevo: {e}")
        return False
