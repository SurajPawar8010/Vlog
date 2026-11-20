import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("InstagramPoster")

class InstagramPoster:
    """
    Direct Instagram Reel Auto-Posting Engine.
    Enables 1-click publishing of rendered daily vlogs directly as Instagram Reels.
    Supports secure local session persistence.
    """

    SESSION_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "instagram_session.json"))

    def __init__(self):
        os.makedirs(os.path.dirname(self.SESSION_FILE), exist_ok=True)
        self.client = None
        self.logged_in = False
        self.username = None
        self._try_load_saved_session()

    def _get_client(self):
        try:
            from instagrapi import Client
            cl = Client()
            cl.delay_range = [1, 3]
            return cl
        except ImportError:
            raise RuntimeError("instagrapi library is not installed. Run: pip install instagrapi")

    def _try_load_saved_session(self):
        """Attempt to restore previously saved Instagram login session."""
        if not os.path.exists(self.SESSION_FILE):
            return

        try:
            with open(self.SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            settings = data.get("settings")
            username = data.get("username")

            if settings and username:
                cl = self._get_client()
                cl.set_settings(settings)
                # Verify session validity
                cl.get_timeline_feed()
                self.client = cl
                self.logged_in = True
                self.username = username
                logger.info(f"Restored Instagram session for @{username}")
        except Exception as e:
            logger.warning(f"Failed to restore Instagram session: {e}")
            self.logged_in = False
            self.username = None

    def get_status(self) -> Dict[str, Any]:
        """Check current Instagram connection status."""
        return {
            "logged_in": self.logged_in,
            "username": self.username
        }

    def _attempt_web_login(self, username: str, password: str, verification_code: Optional[str] = None) -> Optional[str]:
        """
        Authenticate via Instagram Web API using username & password.
        Returns the authenticated sessionid cookie string on success.
        """
        import requests
        import time

        clean_user = username.strip().replace("@", "")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        try:
            r1 = session.get('https://www.instagram.com/accounts/login/', timeout=10)
            csrf_token = session.cookies.get('csrftoken', '') or r1.cookies.get('csrftoken', '')
            if not csrf_token:
                csrf_token = "missing"

            timestamp = int(time.time())
            enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}"

            payload = {
                'username': clean_user,
                'enc_password': enc_password,
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'trustedDeviceRecords': '{}'
            }

            headers = {
                'X-CSRFToken': csrf_token,
                'X-Instagram-AJAX': '1013456789',
                'X-IG-App-ID': '936619743392459',
                'X-ASBD-ID': '129477',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.instagram.com/accounts/login/',
                'Origin': 'https://www.instagram.com',
            }

            res = session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/', data=payload, headers=headers, timeout=15)
            data = res.json()

            if data.get("authenticated"):
                sessionid = session.cookies.get('sessionid')
                if sessionid:
                    return sessionid

            if data.get("two_factor_required"):
                two_factor_info = data.get("two_factor_info", {})
                two_factor_id = two_factor_info.get("two_factor_identifier")

                if verification_code and two_factor_id:
                    # Submit 2FA Code via Web API
                    tf_payload = {
                        'username': clean_user,
                        'verificationCode': verification_code.strip(),
                        'identifier': two_factor_id,
                        'queryParams': '{}'
                    }
                    tf_res = session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/two_factor/', data=tf_payload, headers=headers, timeout=15)
                    tf_data = tf_res.json()
                    if tf_data.get("authenticated"):
                        sessionid = session.cookies.get('sessionid')
                        if sessionid:
                            return sessionid

                raise RuntimeError("2FA_REQUIRED:" + (two_factor_info.get("obfuscated_phone_number") or "your phone"))

            if data.get("message") == "checkpoint_required":
                raise RuntimeError("CHECKPOINT_REQUIRED")

            if data.get("user") is False or data.get("status") == "fail":
                msg = data.get("message") or "Invalid username or password"
                if "password" in msg.lower():
                    raise RuntimeError("Incorrect Instagram password. Please check your spelling.")
                raise RuntimeError(msg)

        except Exception as e:
            err_str = str(e)
            if "2FA_REQUIRED" in err_str or "CHECKPOINT_REQUIRED" in err_str or "Incorrect" in err_str:
                raise e
            logger.warning(f"Web login handshake exception: {e}")

        return None

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verification_code: Optional[str] = None,
        sessionid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log in to Instagram seamlessly using User ID and Password (with smart Web handshake & 2FA support).
        Saves session locally to avoid repeated logins.
        """
        cl = self._get_client()

        # Method 1: Direct Session ID provided
        if sessionid and sessionid.strip():
            clean_session = sessionid.strip()
            try:
                cl.login_by_sessionid(clean_session)
                try:
                    user_info = cl.account_info()
                    clean_user = getattr(user_info, "username", None) or "instagram_user"
                except Exception:
                    clean_user = (username.strip().replace("@", "") if username else "instagram_user")

                self.client = cl
                self.logged_in = True
                self.username = clean_user

                with open(self.SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "username": clean_user,
                        "settings": cl.get_settings()
                    }, f, indent=2)

                return {
                    "status": "success",
                    "message": f"Successfully connected to Instagram as @{clean_user}!",
                    "username": clean_user
                }
            except Exception as e:
                raise RuntimeError(f"Session ID login failed: {str(e)}")

        # Method 2: Username & Password Login
        if not username or not password:
            raise ValueError("Please enter your Instagram Username and Password.")

        clean_user = username.strip().replace("@", "")

        # Step 2A: Try Smart Web Handshake (Bypasses 'version out of date' error 100%)
        try:
            web_sessionid = self._attempt_web_login(clean_user, password, verification_code=verification_code)
            if web_sessionid:
                cl.login_by_sessionid(web_sessionid)
                self.client = cl
                self.logged_in = True
                self.username = clean_user

                with open(self.SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "username": clean_user,
                        "settings": cl.get_settings()
                    }, f, indent=2)

                return {
                    "status": "success",
                    "message": f"Successfully connected to Instagram as @{clean_user}!",
                    "username": clean_user
                }
        except Exception as e:
            err_msg = str(e)
            if "2FA_REQUIRED" in err_msg:
                return {
                    "status": "2fa_required",
                    "message": "2FA Security Code required. Please enter the 6-digit verification code sent to your phone/authenticator.",
                    "username": clean_user
                }
            elif "CHECKPOINT_REQUIRED" in err_msg:
                return {
                    "status": "challenge_required",
                    "message": "Instagram security check: Open your Instagram app on your phone, tap 'This Was Me', then click Connect again.",
                    "username": clean_user
                }
            elif "Incorrect" in err_msg:
                raise RuntimeError("Incorrect Instagram password or username. Please check your credentials.")

        # Step 2B: Fallback to instagrapi Mobile Flow with modern app emulation
        try:
            if verification_code and verification_code.strip():
                cl.login(clean_user, password, verification_code=verification_code.strip())
            else:
                cl.login(clean_user, password)

            self.client = cl
            self.logged_in = True
            self.username = clean_user

            with open(self.SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "username": clean_user,
                    "settings": cl.get_settings()
                }, f, indent=2)

            return {
                "status": "success",
                "message": f"Successfully connected to Instagram as @{clean_user}!",
                "username": clean_user
            }

        except Exception as e:
            error_msg = str(e)
            err_lower = error_msg.lower()

            if "two_factor_required" in err_lower or "2fa" in err_lower or "sms" in err_lower:
                return {
                    "status": "2fa_required",
                    "message": "2FA Security Code required. Please enter the 6-digit code sent to your phone/authenticator app.",
                    "username": clean_user
                }
            elif "challenge_required" in err_lower or "checkpoint" in err_lower:
                return {
                    "status": "challenge_required",
                    "message": "Instagram security check: Open your Instagram mobile app, tap 'This Was Me', and click Connect again.",
                    "username": clean_user
                }
            elif "bad_password" in err_lower or "invalid_credentials" in err_lower or "incorrect" in err_lower:
                raise RuntimeError("Incorrect Instagram password or username. Please check your credentials.")
            elif "please wait a few minutes" in err_lower or "rate_limit" in err_lower:
                raise RuntimeError("Instagram is temporarily rate-limiting logins. Please wait 2 minutes, approve the login prompt in your Instagram app, and try again.")

            raise RuntimeError(f"Instagram Connection Error: {error_msg}")

    def logout(self) -> Dict[str, Any]:
        """Clear saved Instagram session."""
        self.logged_in = False
        self.username = None
        self.client = None
        if os.path.exists(self.SESSION_FILE):
            try:
                os.remove(self.SESSION_FILE)
            except Exception:
                pass
        return {"status": "success", "message": "Logged out from Instagram."}

    def post_reel(self, video_path: str, caption: str = "") -> Dict[str, Any]:
        """
        Post the rendered MP4 video directly as an Instagram Reel.
        """
        if not self.logged_in or not self.client:
            raise RuntimeError("Instagram account is not connected. Please connect your account first.")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # Default caption with trending hashtags if empty
        if not caption.strip():
            caption = (
                "⚡ My Daily Work Vlog ✨\n"
                "Edited with AutoVlog Studio & Heavy Gian Voiceover 🦍🔥\n\n"
                "#dailyvlog #marathivlog #vlog #codinglife #reelsindia #reelsinstagram "
                "#workvlog #gianvoice #creator #productivity"
            )

        # Ensure MoviePy & ImageIO can find FFmpeg
        if "IMAGEIO_FFMPEG_EXE" not in os.environ:
            os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"

        # Generate a high quality JPEG cover thumbnail frame using FFmpeg
        thumb_path = video_path.rsplit(".", 1)[0] + "_ig_cover.jpg"
        cmd_thumb = [
            "ffmpeg", "-y",
            "-ss", "0.5",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            thumb_path
        ]
        try:
            import subprocess
            subprocess.run(cmd_thumb, capture_output=True, check=True)
            if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) < 100:
                thumb_path = None
        except Exception as e:
            logger.warning(f"Could not extract thumbnail with ffmpeg: {e}")
            thumb_path = None

        try:
            logger.info(f"Starting Reel upload to Instagram for video: {video_path}")
            # clip_upload uploads specifically as an Instagram Reel
            if thumb_path and os.path.exists(thumb_path):
                media = self.client.clip_upload(
                    path=video_path,
                    caption=caption,
                    thumbnail=thumb_path
                )
            else:
                media = self.client.clip_upload(
                    path=video_path,
                    caption=caption
                )

            code = getattr(media, "code", "")
            pk = getattr(media, "pk", "")

            if not code and hasattr(media, "dict"):
                m_dict = media.dict()
                code = m_dict.get("code", "")
                pk = m_dict.get("pk", "")

            reel_url = f"https://www.instagram.com/reel/{code}/" if code else f"https://www.instagram.com/{self.username}/"

            return {
                "status": "success",
                "message": "Reel published successfully to Instagram! 🎉",
                "reel_url": reel_url,
                "code": code,
                "pk": str(pk)
            }

        except Exception as e:
            logger.error(f"Failed to post Reel: {e}")
            raise RuntimeError(f"Failed to post Reel to Instagram: {str(e)}")
        finally:
            if thumb_path and os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except Exception:
                    pass

# Global singleton
instagram_poster = InstagramPoster()
