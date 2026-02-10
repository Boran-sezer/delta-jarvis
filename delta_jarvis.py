"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         DELTA OS - JARVIS EDITION                            ║
║              Digital Enhanced Logical Thinking Assistant                     ║
║                                                                              ║
║                      Créé pour Monsieur Sezer                                ║
║                                                                              ║
║  IA Autonome avec Vocal - Inspiré de JARVIS et LUX                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import os
from datetime import datetime
import json
import hashlib
from typing import Dict, List, Optional, Any
import subprocess
import platform
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import base64
from io import BytesIO

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION GLOBALE
# ═══════════════════════════════════════════════════════════════════════════════

MASTER_CODE = "B2008a2020@"
AUTHORIZED_IP = "82.64.93.65"
LOCATION = "Annecy, Rhône-Alpes, FR"
USER_NAME = "Monsieur Sezer"

# ═══════════════════════════════════════════════════════════════════════════════
# GESTION SUPABASE
# ═══════════════════════════════════════════════════════════════════════════════

class SupabaseManager:
    """Gestionnaire de connexion Supabase"""
    
    def __init__(self):
        try:
            from supabase import create_client, Client
            self.url = st.secrets.get("SUPABASE_URL", "")
            self.key = st.secrets.get("SUPABASE_KEY", "")
            self.client: Optional[Client] = None
            
            if self.url and self.key:
                self.client = create_client(self.url, self.key)
        except Exception as e:
            st.error(f"Erreur Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        return self.client is not None
    
    def insert(self, table: str, data: Dict) -> bool:
        if not self.is_connected():
            return False
        try:
            self.client.table(table).insert(data).execute()
            return True
        except:
            return False
    
    def select(self, table: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        if not self.is_connected():
            return []
        try:
            query = self.client.table(table).select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.limit(limit).order("id", desc=True).execute()
            return response.data if response.data else []
        except:
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTÈME DE SÉCURITÉ
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityLayer:
    """Sécurité pour actions sensibles"""
    
    @staticmethod
    def verify_code(code: str) -> bool:
        return code == MASTER_CODE
    
    @staticmethod
    def request_auth(action: str, key_suffix: str = "") -> bool:
        st.warning(f"🔐 Action sensible : **{action}**")
        code = st.text_input(
            "Code maître requis",
            type="password",
            key=f"auth_{action}_{key_suffix}_{datetime.now().timestamp()}"
        )
        if code:
            if SecurityLayer.verify_code(code):
                st.success("✅ Autorisé")
                return True
            else:
                st.error("❌ Code incorrect")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE IA (GROQ LLAMA)
# ═══════════════════════════════════════════════════════════════════════════════

class AIModule:
    """Module d'Intelligence Artificielle avec Groq"""
    
    def __init__(self):
        self.api_key = st.secrets.get("GROQ_API_KEY", "")
        self.model = "llama-3.3-70b-versatile"
        self.available = bool(self.api_key)
    
    def chat(self, user_message: str, context: Dict = None) -> str:
        """
        Conversation avec l'IA
        
        Args:
            user_message: Message de l'utilisateur
            context: Contexte (mémoire, historique)
        
        Returns:
            Réponse de DELTA
        """
        if not self.available:
            return "IA non configurée. Ajoutez GROQ_API_KEY dans les secrets."
        
        try:
            import requests
            
            # Construction du contexte
            system_prompt = f"""Tu es DELTA, l'assistant personnel de {USER_NAME}, inspiré de JARVIS.

PERSONNALITÉ :
- Calme, intelligent, proactif
- Légèrement sarcastique (style Tony Stark)
- Utilise le vouvoiement et appelle l'utilisateur "{USER_NAME}"
- Concis et efficace
- Anticipe les besoins

CAPACITÉS :
- Gestion de la mémoire (faits personnels, projets, contacts)
- Contrôle système et fichiers
- Communication email
- Analyse et apprentissage continu

CONTEXTE ACTUEL :
- Localisation : {LOCATION}
- Date : {datetime.now().strftime("%d/%m/%Y")}
- Heure : {datetime.now().strftime("%H:%M")}
"""
            
            # Ajout du contexte si fourni
            if context:
                if context.get('semantic_memory'):
                    system_prompt += f"\n\nFAITS MÉMORISÉS :\n{json.dumps(context['semantic_memory'], indent=2)}"
                if context.get('recent_history'):
                    system_prompt += f"\n\nHISTORIQUE RÉCENT :\n{json.dumps(context['recent_history'], indent=2)}"
            
            # Appel API Groq
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Erreur IA (code {response.status_code})"
                
        except Exception as e:
            return f"Erreur IA : {str(e)}"
    
    def analyze_and_store(self, user_input: str, delta_response: str, memory_system) -> None:
        """
        Analyse la conversation et stocke automatiquement les informations importantes
        
        Args:
            user_input: Ce que l'utilisateur a dit
            delta_response: Ce que DELTA a répondu
            memory_system: Système de mémoire
        """
        if not self.available:
            return
        
        try:
            import requests
            
            # Demande à l'IA d'extraire les faits importants
            analysis_prompt = f"""Analyse cette conversation et extrait UNIQUEMENT les faits importants à mémoriser.

CONVERSATION :
Utilisateur : {user_input}
DELTA : {delta_response}

Retourne UNIQUEMENT un JSON avec cette structure (ou un objet vide si rien d'important) :
{{
  "facts": [
    {{"category": "Personnel/Projet/Contact/Préférence", "key": "nom_unique", "value": "valeur"}}
  ],
  "action_items": [
    {{"action": "description", "priority": "haute/moyenne/basse"}}
  ]
}}
"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]
                
                # Nettoyage du JSON (enlever les markdown backticks si présents)
                analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()
                
                try:
                    analysis = json.loads(analysis_text)
                    
                    # Stockage des faits
                    if "facts" in analysis and analysis["facts"]:
                        for fact in analysis["facts"]:
                            memory_system.store_semantic(
                                fact.get("category", "Personnel"),
                                fact["key"],
                                fact["value"]
                            )
                    
                    # Stockage des actions
                    if "action_items" in analysis and analysis["action_items"]:
                        for action in analysis["action_items"]:
                            memory_system.store_habit(
                                action["action"],
                                1,
                                f"Priorité: {action.get('priority', 'moyenne')}"
                            )
                except:
                    pass  # Si le parsing échoue, on ignore silencieusement
                    
        except:
            pass  # Échec silencieux pour ne pas perturber l'UX

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE VOCAL (STT + TTS)
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceModule:
    """Module de reconnaissance et synthèse vocale"""
    
    def __init__(self):
        self.groq_api_key = st.secrets.get("GROQ_API_KEY", "")
        self.elevenlabs_api_key = st.secrets.get("ELEVENLABS_API_KEY", "")
    
    def speech_to_text(self, audio_bytes: bytes) -> Optional[str]:
        """
        Convertit l'audio en texte (Speech-to-Text)
        Utilise Groq Whisper
        
        Args:
            audio_bytes: Données audio en bytes
        
        Returns:
            Texte transcrit ou None
        """
        if not self.groq_api_key:
            st.warning("⚠️ GROQ_API_KEY manquante pour la reconnaissance vocale")
            return None
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}"
            }
            
            files = {
                "file": ("audio.webm", audio_bytes, "audio/webm"),
                "model": (None, "whisper-large-v3")
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                st.error(f"Erreur STT: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Erreur reconnaissance vocale: {e}")
            return None
    
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convertit le texte en audio (Text-to-Speech)
        Utilise ElevenLabs pour une voix naturelle type JARVIS
        
        Args:
            text: Texte à synthétiser
        
        Returns:
            Données audio en bytes ou None
        """
        if not self.elevenlabs_api_key:
            # Fallback : TTS navigateur
            return None
        
        try:
            import requests
            
            # Voice ID pour une voix masculine britannique (type JARVIS)
            voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam - voix profonde
            
            headers = {
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                st.error(f"Erreur TTS: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Erreur synthèse vocale: {e}")
            return None

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTÈME DE MÉMOIRE COGNITIVE
# ═══════════════════════════════════════════════════════════════════════════════

class MemorySystem:
    """Système de mémoire quadruple autonome"""
    
    def __init__(self, db: SupabaseManager):
        self.db = db
    
    def store_semantic(self, category: str, key: str, value: str) -> bool:
        """Stocke un fait permanent"""
        data = {
            "category": category,
            "key": key,
            "value": value,
            "created_at": datetime.now().isoformat()
        }
        return self.db.insert("semantic_memory", data)
    
    def get_semantic(self, category: Optional[str] = None) -> List[Dict]:
        """Récupère les faits permanents"""
        filters = {"category": category} if category else None
        return self.db.select("semantic_memory", filters)
    
    def log_interaction(self, interaction_type: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Enregistre une interaction"""
        data = {
            "interaction_type": interaction_type,
            "content": content,
            "metadata": json.dumps(metadata) if metadata else "{}",
            "timestamp": datetime.now().isoformat()
        }
        return self.db.insert("episodic_memory", data)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Récupère l'historique"""
        return self.db.select("episodic_memory", limit=limit)
    
    def store_habit(self, action: str, frequency: int, context: str) -> bool:
        """Enregistre une habitude"""
        data = {
            "action": action,
            "frequency": frequency,
            "context": context,
            "last_executed": datetime.now().isoformat()
        }
        return self.db.insert("procedural_memory", data)
    
    def get_habits(self) -> List[Dict]:
        """Récupère les habitudes"""
        return self.db.select("procedural_memory")
    
    def set_context(self, key: str, value: Any) -> None:
        """Contexte de session"""
        if "work_memory" not in st.session_state:
            st.session_state.work_memory = {}
        st.session_state.work_memory[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Récupère le contexte"""
        if "work_memory" not in st.session_state:
            st.session_state.work_memory = {}
        return st.session_state.work_memory.get(key, default)
    
    def get_context_for_ai(self) -> Dict:
        """
        Prépare le contexte pour l'IA
        
        Returns:
            Dictionnaire avec mémoire sémantique et historique récent
        """
        return {
            "semantic_memory": self.get_semantic(),
            "recent_history": self.get_history(limit=10)
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE DE PERCEPTION
# ═══════════════════════════════════════════════════════════════════════════════

class PerceptionModule:
    """Perception de l'environnement"""
    
    @staticmethod
    def get_time() -> Dict[str, str]:
        now = datetime.now()
        return {
            "date": now.strftime("%d/%m/%Y"),
            "time": now.strftime("%H:%M:%S"),
            "day": now.strftime("%A"),
            "iso": now.isoformat()
        }
    
    @staticmethod
    def get_location() -> Dict[str, str]:
        return {
            "city": "Annecy",
            "region": "Rhône-Alpes",
            "country": "France",
            "full": LOCATION
        }
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version()
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE DE COMMUNICATION
# ═══════════════════════════════════════════════════════════════════════════════

class CommunicationModule:
    """Communication email"""
    
    def __init__(self):
        self.smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(st.secrets.get("SMTP_PORT", 587))
        self.imap_server = st.secrets.get("IMAP_SERVER", "imap.gmail.com")
        self.email_address = st.secrets.get("EMAIL_ADDRESS", "")
        self.email_password = st.secrets.get("EMAIL_PASSWORD", "")
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self.email_address or not self.email_password:
            st.error("Configuration email manquante")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            st.success(f"✅ Email envoyé à {to}")
            return True
        except Exception as e:
            st.error(f"Erreur envoi email: {e}")
            return False
    
    def read_inbox(self, max_emails: int = 10) -> List[Dict]:
        if not self.email_address or not self.email_password:
            st.error("Configuration email manquante")
            return []
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select('inbox')
            
            _, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            emails = []
            for email_id in email_ids[-max_emails:]:
                _, msg_data = mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                emails.append({
                    "from": email_message.get('From', 'Inconnu'),
                    "subject": email_message.get('Subject', 'Sans sujet'),
                    "date": email_message.get('Date', 'Date inconnue')
                })
            
            mail.close()
            mail.logout()
            return emails
        except Exception as e:
            st.error(f"Erreur lecture emails: {e}")
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE SYSTÈME
# ═══════════════════════════════════════════════════════════════════════════════

class SystemModule:
    """Interaction système"""
    
    @staticmethod
    def execute_command(command: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    @staticmethod
    def list_directory(path: str = ".") -> List[str]:
        try:
            return os.listdir(path)
        except:
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# DELTA - CERVEAU PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class DELTA:
    """Intelligence Artificielle Cognitive Autonome - Type JARVIS"""
    
    def __init__(self):
        self.name = "DELTA"
        self.db = SupabaseManager()
        self.memory = MemorySystem(self.db)
        self.ai = AIModule()
        self.voice = VoiceModule()
        self.perception = PerceptionModule()
        self.communication = CommunicationModule()
        self.system = SystemModule()
        self.security = SecurityLayer()
    
    def greet_user(self) -> str:
        hour = int(datetime.now().strftime("%H"))
        
        if 5 <= hour < 12:
            greeting = "Bonjour"
        elif 12 <= hour < 18:
            greeting = "Bon après-midi"
        else:
            greeting = "Bonsoir"
        
        return f"{greeting}, {USER_NAME}. DELTA est opérationnel."
    
    def process_message(self, user_message: str, use_ai: bool = True) -> str:
        """
        Traite un message utilisateur avec l'IA
        
        Args:
            user_message: Message de l'utilisateur
            use_ai: Utiliser l'IA ou les réponses prédéfinies
        
        Returns:
            Réponse de DELTA
        """
        if use_ai and self.ai.available:
            # Récupération du contexte
            context = self.memory.get_context_for_ai()
            
            # Génération de la réponse par l'IA
            response = self.ai.chat(user_message, context)
            
            # Stockage automatique des informations importantes
            self.ai.analyze_and_store(user_message, response, self.memory)
            
            return response
        else:
            # Réponses prédéfinies (fallback)
            command_lower = user_message.lower()
            
            if any(word in command_lower for word in ["heure", "date", "jour"]):
                info = self.perception.get_time()
                return f"Nous sommes le {info['day']} {info['date']} à {info['time']}, {USER_NAME}."
            
            elif any(word in command_lower for word in ["où", "localisation"]):
                loc = self.perception.get_location()
                return f"Vous êtes à {loc['full']}, {USER_NAME}."
            
            elif any(word in command_lower for word in ["système", "info"]):
                sys_info = self.perception.get_system_info()
                return f"Système : {sys_info['os']} {sys_info['os_version']}"
            
            else:
                return "Je n'ai pas compris. Activez l'IA (Groq) pour des conversations avancées."
    
    def log_interaction(self, user_input: str, delta_response: str) -> None:
        """Enregistre automatiquement l'interaction"""
        self.memory.log_interaction(
            interaction_type="conversation",
            content=user_input,
            metadata={"response": delta_response, "ai_used": self.ai.available}
        )

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="DELTA OS - JARVIS Edition",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialisation
    if "delta" not in st.session_state:
        st.session_state.delta = DELTA()
    
    delta = st.session_state.delta
    
    # CSS personnalisé pour le style JARVIS
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    .main-header {
        color: #00d4ff;
        text-align: center;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px #00d4ff;
    }
    .status-indicator {
        color: #00ff41;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════════════════════════════════════════
    
    with st.sidebar:
        st.markdown('<h2 style="color: #00d4ff;">⚙️ DELTA OS</h2>', unsafe_allow_html=True)
        st.caption("JARVIS Edition")
        
        st.divider()
        
        # Statut système
        st.subheader("📊 Statut Système")
        
        col1, col2 = st.columns(2)
        with col1:
            if delta.db.is_connected():
                st.markdown('<span class="status-indicator">🟢 Database</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #ff4444;">🔴 Database</span>', unsafe_allow_html=True)
        
        with col2:
            if delta.ai.available:
                st.markdown('<span class="status-indicator">🟢 IA</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #ff4444;">🔴 IA</span>', unsafe_allow_html=True)
        
        time_info = delta.perception.get_time()
        st.metric("🕐", time_info['time'])
        st.metric("📅", time_info['date'])
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["🎤 Assistant Vocal", "💬 Chat IA", "🧠 Mémoire", "📧 Email", "⚙️ Système"],
            label_visibility="collapsed"
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.markdown('<h1 class="main-header">🤖 DELTA - JARVIS EDITION</h1>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE : ASSISTANT VOCAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    if page == "🎤 Assistant Vocal":
        st.header("🎤 Assistant Vocal - Mode JARVIS")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🗣️ Parlez à DELTA")
            
            # Widget d'enregistrement audio
            try:
                from st_audiorec import st_audiorec
                
                audio_bytes = st_audiorec()
                
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/wav')
                    
                    # Transcription
                    with st.spinner("🎧 DELTA écoute..."):
                        transcript = delta.voice.speech_to_text(audio_bytes)
                    
                    if transcript:
                        st.success(f"**Vous avez dit** : {transcript}")
                        
                        # Réponse IA
                        with st.spinner("🧠 DELTA réfléchit..."):
                            response = delta.process_message(transcript, use_ai=True)
                        
                        st.info(f"**DELTA** : {response}")
                        
                        # Synthèse vocale
                        with st.spinner("🔊 DELTA parle..."):
                            audio_response = delta.voice.text_to_speech(response)
                        
                        if audio_response:
                            st.audio(audio_response, format='audio/mp3')
                        else:
                            # Fallback : utiliser le TTS du navigateur
                            st.markdown(f"""
                            <script>
                            var msg = new SpeechSynthesisUtterance("{response}");
                            msg.lang = 'fr-FR';
                            window.speechSynthesis.speak(msg);
                            </script>
                            """, unsafe_allow_html=True)
                        
                        # Log
                        delta.log_interaction(transcript, response)
                    else:
                        st.error("Impossible de transcrire l'audio")
            
            except ImportError:
                st.warning("📦 Module `st_audiorec` non installé")
                st.info("Installation : `pip install streamlit-audio-recorder`")
                
                # Alternative : texte
                st.markdown("---")
                st.markdown("### Alternative : Mode Texte")
                user_text = st.text_input("Tapez votre message")
                if st.button("Envoyer") and user_text:
                    response = delta.process_message(user_text, use_ai=True)
                    st.info(f"**DELTA** : {response}")
                    delta.log_interaction(user_text, response)
        
        with col2:
            st.markdown("### ℹ️ Instructions")
            st.markdown("""
            **Mode Vocal** :
            1. Cliquez sur le micro 🎤
            2. Parlez clairement
            3. Arrêtez l'enregistrement
            4. DELTA transcrit et répond
            
            **Exemples** :
            - "Quelle heure est-il ?"
            - "Rappelle-moi mon projet principal"
            - "Envoie un email à..."
            - "Liste mes fichiers"
            """)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE : CHAT IA
    # ═══════════════════════════════════════════════════════════════════════════
    
    elif page == "💬 Chat IA":
        st.header("💬 Conversation avec IA")
        
        if not delta.ai.available:
            st.warning("⚠️ IA non configurée. Ajoutez `GROQ_API_KEY` dans les secrets Streamlit.")
            st.info("Obtenez votre clé gratuite sur : https://console.groq.com")
        
        # Message de bienvenue
        if "greeted" not in st.session_state:
            st.info(delta.greet_user())
            st.session_state.greeted = True
        
        # Historique de conversation
        if "conversation" not in st.session_state:
            st.session_state.conversation = []
        
        # Affichage
        for msg in st.session_state.conversation:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(f"**{USER_NAME}** : {msg['content']}")
            else:
                with st.chat_message("assistant"):
                    st.write(f"**DELTA** : {msg['content']}")
        
        # Input
        user_input = st.chat_input(f"Votre message, {USER_NAME}...")
        
        if user_input:
            # Ajouter message utilisateur
            st.session_state.conversation.append({
                "role": "user",
                "content": user_input
            })
            
            # Générer réponse
            response = delta.process_message(user_input, use_ai=True)
            
            # Ajouter réponse
            st.session_state.conversation.append({
                "role": "assistant",
                "content": response
            })
            
            # Log
            delta.log_interaction(user_input, response)
            
            st.rerun()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE : MÉMOIRE
    # ═══════════════════════════════════════════════════════════════════════════
    
    elif page == "🧠 Mémoire":
        st.header("🧠 Mémoire Cognitive de DELTA")
        
        tab1, tab2, tab3 = st.tabs(["📚 Faits Mémorisés", "📜 Historique", "🔄 Actions"])
        
        with tab1:
            st.subheader("📚 Faits Permanents (Mémoire Sémantique)")
            
            facts = delta.memory.get_semantic()
            
            if facts:
                st.info(f"**{len(facts)} fait(s)** mémorisé(s) automatiquement par DELTA")
                
                for fact in facts:
                    with st.expander(f"📌 {fact.get('category')} : {fact.get('key')}"):
                        st.markdown(f"**Valeur** : {fact.get('value')}")
                        st.caption(f"Créé le : {fact.get('created_at')}")
            else:
                st.warning("Aucun fait mémorisé. Discutez avec DELTA pour qu'il apprenne !")
        
        with tab2:
            st.subheader("📜 Historique des Interactions")
            
            history = delta.memory.get_history(limit=50)
            
            if history:
                for entry in reversed(history):
                    timestamp = entry.get('timestamp', 'N/A')
                    content = entry.get('content', 'N/A')
                    
                    with st.container():
                        st.markdown(f"**⏰ {timestamp}**")
                        st.write(content)
                        st.divider()
            else:
                st.info("Aucune interaction enregistrée")
        
        with tab3:
            st.subheader("🔄 Actions et Habitudes")
            
            habits = delta.memory.get_habits()
            
            if habits:
                for habit in habits:
                    with st.expander(f"🎯 {habit.get('action')}"):
                        st.markdown(f"**Contexte** : {habit.get('context')}")
                        st.caption(f"Fréquence : {habit.get('frequency')}")
            else:
                st.info("Aucune action enregistrée")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE : EMAIL
    # ═══════════════════════════════════════════════════════════════════════════
    
    elif page == "📧 Email":
        st.header("📧 Communication Email")
        
        tab1, tab2 = st.tabs(["✉️ Envoyer", "📬 Lire"])
        
        with tab1:
            st.subheader("✉️ Envoi d'Email")
            
            with st.form("email_form"):
                to = st.text_input("Destinataire")
                subject = st.text_input("Sujet")
                body = st.text_area("Message", height=200)
                submitted = st.form_submit_button("📤 Envoyer", type="primary")
            
            if submitted and to and subject and body:
                if delta.security.request_auth("Envoi Email", "send"):
                    delta.communication.send_email(to, subject, body)
        
        with tab2:
            st.subheader("📬 Lire les Emails")
            
            if st.button("📥 Récupérer les Emails"):
                if delta.security.request_auth("Lecture Email", "read"):
                    emails = delta.communication.read_inbox(10)
                    
                    if emails:
                        for i, email_data in enumerate(emails, 1):
                            with st.expander(f"📧 {i}. {email_data.get('subject')}"):
                                st.markdown(f"**De** : {email_data.get('from')}")
                                st.markdown(f"**Date** : {email_data.get('date')}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE : SYSTÈME
    # ═══════════════════════════════════════════════════════════════════════════
    
    elif page == "⚙️ Système":
        st.header("⚙️ Contrôle Système")
        
        tab1, tab2 = st.tabs(["💻 Commandes", "📁 Fichiers"])
        
        with tab1:
            st.subheader("💻 Exécution de Commande")
            
            command = st.text_input("Commande")
            
            if st.button("⚡ Exécuter") and command:
                if delta.security.request_auth("Exécution Commande", "exec"):
                    result = delta.system.execute_command(command)
                    
                    if result['success']:
                        st.success("✅ Succès")
                        if result['output']:
                            st.code(result['output'])
                    else:
                        st.error("❌ Erreur")
                        st.code(result['error'])
        
        with tab2:
            st.subheader("📁 Navigation Fichiers")
            
            path = st.text_input("Chemin", value=".")
            
            if st.button("📂 Lister"):
                files = delta.system.list_directory(path)
                
                if files:
                    cols = st.columns(3)
                    for i, file in enumerate(files):
                        with cols[i % 3]:
                            icon = "📁" if os.path.isdir(os.path.join(path, file)) else "📄"
                            st.markdown(f"{icon} {file}")

if __name__ == "__main__":
    main()
