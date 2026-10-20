import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from src.config.settings import settings
from src.models.match import Match
from src.utils.date_utils import format_report_date, format_date_dots, format_date_range_readable
from src.utils.logger import logger

class EmailService:
    def __init__(self):
        self.settings = settings

    def generate_html(self, date_str: str, football_matches: List[Match], basketball_matches: List[Match], is_empty: bool = False, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        start_date = start_date or date_str
        end_date = end_date or date_str
        is_range = start_date != end_date
        if is_range:
            report_date_readable = format_date_range_readable(start_date, end_date)
            report_date_dots = f"{format_date_dots(start_date)} - {format_date_dots(end_date)}"
        else:
            report_date_readable = format_report_date(date_str)
            report_date_dots = format_date_dots(date_str)

        # Template helper for match card
        def date_label(match: Match) -> str:
            try:
                d = format_date_dots(match.match_date) if match.match_date else ""
            except Exception:
                d = match.match_date or ""
            t = f" • {match.start_time}" if match.start_time else ""
            return f"{d}{t}" if d else ""

        def render_match_row(match: Match, show_date: bool = False) -> str:
            is_bjk = match.is_besiktas_match
            bg_style = "background: #fffdf2; border: 1.5px solid #d4af37; box-shadow: 0 2px 6px rgba(212,175,55,0.2);" if is_bjk else "background: #ffffff; border: 1px solid #e2e8f0;"
            star_badge = '<span style="color:#eab308; font-size:1.15em; margin-right:4px;">⭐</span>' if is_bjk else ''
            bjk_tag = '<div style="font-size: 11px; font-weight: 700; color: #b45309; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">BEŞİKTAŞ MAÇI</div>' if is_bjk else ''
            
            home_bjk_weight = "font-weight: 700; color: #0f172a;" if match.is_home_besiktas else "color: #334155;"
            away_bjk_weight = "font-weight: 700; color: #0f172a;" if match.is_away_besiktas else "color: #334155;"
            
            home_logo_img = f'<img src="{match.home_logo}" style="width:20px;height:20px;object-fit:contain;vertical-align:middle;margin-right:6px;">' if match.home_logo else ''
            away_logo_img = f'<img src="{match.away_logo}" style="width:20px;height:20px;object-fit:contain;vertical-align:middle;margin-left:6px;">' if match.away_logo else ''

            score_home = match.home_score if match.home_score is not None else "-"
            score_away = match.away_score if match.away_score is not None else "-"
            date_line = f'<div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">📅 {date_label(match)}</div>' if show_date and date_label(match) else ""

            return f"""
            <div style="margin-bottom: 10px; padding: 12px 16px; border-radius: 8px; {bg_style}">
                {bjk_tag}
                {date_line}
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <tr>
                        <td width="42%" align="right" style="font-size: 14px; {home_bjk_weight} padding-right: 12px;">
                            {star_badge if match.is_home_besiktas else ""}{match.home_team} {home_logo_img}
                        </td>
                        <td width="16%" align="center" style="background: #0f172a; color: #ffffff; font-size: 15px; font-weight: 700; padding: 6px 10px; border-radius: 6px; white-space: nowrap;">
                            {score_home} - {score_away}
                        </td>
                        <td width="42%" align="left" style="font-size: 14px; {away_bjk_weight} padding-left: 12px;">
                            {away_logo_img} {match.away_team}{star_badge if match.is_away_besiktas else ""}
                        </td>
                    </tr>
                </table>
            </div>
            """

        def render_section(title: str, color: str, border: str, matches: List[Match], empty_text: str) -> str:
            section = f"""
            <div style="margin-top: 24px;">
                <div style="display: flex; align-items: center; border-bottom: 2px solid {border}; padding-bottom: 6px; margin-bottom: 14px;">
                    <h2 style="font-size: 16px; font-weight: 700; color: {color}; margin: 0;">{title}</h2>
                </div>
            """
            if not matches:
                section += f"""
                <p style="color: #64748b; font-size: 13px; margin: 8px 0;">{empty_text}</p>
            </div>
            """
                return section
            # Group by date for weekly reports
            ordered = sorted(matches, key=lambda m: (m.match_date or "", m.start_time or ""))
            last_date = None
            for m in ordered:
                if is_range and m.match_date and m.match_date != last_date:
                    try:
                        readable = format_report_date(m.match_date)
                    except Exception:
                        readable = m.match_date
                    section += f"""
                <div style="font-size: 12px; font-weight: 700; color: #475569; margin: 12px 0 8px 0;">📅 {readable}</div>
                """
                    last_date = m.match_date
                section += render_match_row(m, show_date=not is_range)
            section += "</div>"
            return section

        # Football section
        football_html = render_section(
            "⚽ TÜRKİYE SÜPER LİG", "#0369a1", "#0284c7", football_matches,
            "Bu dönemde bu ligde tamamlanmış maç bulunmamaktadır."
        )

        # Basketball section
        basketball_html = render_section(
            "🏀 TÜRKİYE BASKETBOL SÜPER LİGİ (BSL)", "#c2410c", "#ea580c", basketball_matches,
            "Bu dönemde bu ligde tamamlanmış maç bulunmamaktadır."
        )

        # Empty state override if requested
        body_content = ""
        if is_empty:
            empty_period = report_date_readable if is_range else "Bugün"
            body_content = f"""
            <div style="padding: 30px; text-align: center; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1; margin: 20px 0;">
                <p style="font-size: 16px; color: #475569; margin: 0 0 8px 0; font-weight: 600;">Tamamlanan Maç Bulunamadı</p>
                <p style="font-size: 14px; color: #64748b; margin: 0;">{empty_period} döneminde Türkiye Süper Lig ve Basketbol Süper Ligi'nde tamamlanan maç bulunmamaktadır.</p>
            </div>
            """
        else:
            body_content = football_html + basketball_html

        # SEG_Maçkolik web linki
        report_url = f"{self.settings.app_url}/?start={start_date}&end={end_date}"
        web_link_box = f"""
        <div style="margin-top: 20px; padding: 14px; text-align: center; background: #fff7ed; border-radius: 8px; border: 1px solid #fed7aa;">
            <p style="font-size: 13px; color: #9a3412; margin: 0 0 8px 0; font-weight: 600;">Maçları filtreleyip incelemek ister misiniz?</p>
            <a href="{report_url}" style="display: inline-block; padding: 8px 20px; background: #ea580c; color: #ffffff; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 700;">
                SEG_Maçkolik'te Görüntüle
            </a>
        </div>
        """
        body_content += web_link_box

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Türkiye Spor Sonuçları - {report_date_dots}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f1f5f9; padding: 24px 12px;">
        <tr>
            <td align="center">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px; text-align: center;">
                            <h1 style="color: #ffffff; font-size: 20px; font-weight: 800; margin: 0 0 6px 0; letter-spacing: -0.3px;">
                                TÜRKİYE SPOR SONUÇLARI
                            </h1>
                            <div style="display: inline-block; background: rgba(255,255,255,0.15); color: #cbd5e1; font-size: 13px; font-weight: 500; padding: 4px 12px; border-radius: 20px;">
                                📅 {report_date_readable}
                            </div>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 24px;">
                            {body_content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; text-align: center; color: #64748b; font-size: 12px;">
                            <p style="margin: 0 0 6px 0;"><strong>Rapor Tarihi:</strong> {report_date_readable}</p>
                            <p style="margin: 0 0 10px 0;"><strong>Veri Kaynağı:</strong> SportScore API</p>
                            <div style="margin-top: 10px;">
                                <a href="https://sportscore.com/" rel="dofollow" title="Sports data by SportScore" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: #0a1e3d; color: #ffffff; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;">
                                    Powered by SportScore
                                </a>
                            </div>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html

    def generate_plain_text(self, date_str: str, football_matches: List[Match], basketball_matches: List[Match], is_empty: bool = False, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        start_date = start_date or date_str
        end_date = end_date or date_str
        is_range = start_date != end_date
        if is_range:
            report_date_readable = format_date_range_readable(start_date, end_date)
            report_date_dots = f"{format_date_dots(start_date)} - {format_date_dots(end_date)}"
        else:
            report_date_readable = format_report_date(date_str)
            report_date_dots = format_date_dots(date_str)

        lines = [
            f"Türkiye Spor Sonuçları - {report_date_dots}",
            "=" * 36,
            ""
        ]

        def append_grouped(header: str, matches: List[Match]):
            lines.append(header)
            ordered = sorted(matches, key=lambda m: (m.match_date or "", m.start_time or ""))
            last_date = None
            for m in ordered:
                if is_range and m.match_date and m.match_date != last_date:
                    try:
                        readable = format_report_date(m.match_date)
                    except Exception:
                        readable = m.match_date
                    lines.append(f"-- {readable} --")
                    last_date = m.match_date
                if not is_range:
                    lines.append(m.to_text_summary())
                else:
                    try:
                        d = format_date_dots(m.match_date) if m.match_date else ""
                    except Exception:
                        d = m.match_date or ""
                    lines.append(f"[{d}] {m.to_text_summary()}")
            lines.append("")

        if is_empty:
            lines.append("Bu dönemde takip edilen liglerde tamamlanan maç bulunmamaktadır.")
        else:
            if football_matches:
                append_grouped("[ Futbol: Türkiye Süper Lig ]", football_matches)

            if basketball_matches:
                append_grouped("[ Basketbol: Türkiye Basketbol Süper Ligi ]", basketball_matches)

        lines.extend([
            "=" * 36,
            f"Rapor tarihi: {report_date_readable}",
            f"Web'de görüntüle (SEG_Maçkolik): {settings.app_url}/?start={start_date}&end={end_date}",
            "Veri kaynağı: SportScore (https://sportscore.com/)",
            ""
        ])
        return "\n".join(lines)

    def send_email(self, subject: str, html_content: str, plain_content: str) -> bool:
        if self.settings.test_mode:
            logger.info("[TEST_MODE] Email not sent via SMTP. Writing to preview_report.html...")
            with open("preview_report.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("[TEST_MODE] Saved report HTML to preview_report.html")
            print("\n" + "=" * 50)
            print(f"Subject: {subject}")
            print("=" * 50)
            print(plain_content)
            print("=" * 50 + "\n")
            return True

        if not self.settings.is_smtp_configured():
            logger.error("SMTP credentials are not configured in .env! Cannot send email.")
            return False

        logger.info(f"Connecting to SMTP server {self.settings.smtp_host}:{self.settings.smtp_port}...")
        try:
            recipients = [addr.strip() for addr in self.settings.email_to.split(",") if addr.strip()]
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.settings.email_from
            msg["To"] = ", ".join(recipients)

            part1 = MIMEText(plain_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            if self.settings.smtp_port == 465:
                # SSL
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as server:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                    server.sendmail(self.settings.email_from, recipients, msg.as_string())
            else:
                # TLS (port 587 or standard)
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as server:
                    if self.settings.smtp_use_tls:
                        server.starttls()
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                    server.sendmail(self.settings.email_from, recipients, msg.as_string())

            logger.info("Email sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

email_service = EmailService()
