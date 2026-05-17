from app import app, db, Admin, User, RecruitmentInfo, Service, Project, News, Client, Newsletter, RecruitmentQuestion, Application, Inquiry, EmailTemplate, Setting
from werkzeug.security import generate_password_hash

def init_data():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()

        print("Seeding Admin account...")
        # Create default admin account
        admin = Admin(
            username='admin',
            password=generate_password_hash('cvisual2026')
        )
        db.session.add(admin)

        print("Seeding Global Settings...")
        # Create default settings
        settings = [
            Setting(key='logo_url', value='https://cvisual-backend.onrender.com/api/uploads/logo.jpg')
        ]
        for s in settings:
            db.session.add(s)

        print("Seeding Email Templates...")
        # Default Templates
        templates = [
            EmailTemplate(
                key="recruitment_received",
                name="Candidature Reçue",
                subject="CVisual - Candidature Reçue pour le poste de {job_title}",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #1e3a8a; text-align: center; font-size: 20px; margin-bottom: 15px;">Merci pour votre candidature !</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous avons bien reçu votre candidature pour le poste de <strong>{job_title}</strong> chez CVisual Agency.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Notre équipe de recrutement va examiner attentivement vos informations ainsi que vos réponses personnalisées. Si votre profil correspond à nos besoins, nous vous contacterons très prochainement pour un entretien.</p>
    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #1f2937;"><strong>Récapitulatif de vos informations :</strong></p>
        <ul style="margin: 5px 0 0 0; padding-left: 20px; font-size: 13px; color: #4b5563; line-height: 1.5;">
            <li>WhatsApp : {whatsapp}</li>
            <li>TikTok : {tiktok}</li>
        </ul>
    </div>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">À très bientôt,</p>
    <p style="color: #1e3a8a; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0 15px 0;">
    <p style="text-align: center; font-size: 12px; color: #9ca3af; margin: 0;">Ce message a été envoyé automatiquement. Merci de ne pas y répondre directement.</p>
</div>""",
                variables="full_name, job_title, whatsapp, tiktok"
            ),
            EmailTemplate(
                key="recruitment_interview",
                name="Invitation Entretien",
                subject="CVisual - Invitation à un entretien pour le poste de {job_title}",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #2563eb; text-align: center; font-size: 20px; margin-bottom: 15px;">Bonne nouvelle ! Votre profil nous intéresse.</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Suite à l'étude de votre candidature pour le poste de <strong>{job_title}</strong>, nous avons le plaisir de vous inviter à un entretien.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Cet entretien sera l'occasion de faire connaissance, d'en apprendre davantage sur votre parcours et de discuter des modalités de notre collaboration.</p>
    <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 15px; border-radius: 0 8px 8px 0; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #1e40af;"><strong>Prochaine étape :</strong></p>
        <p style="margin: 5px 0 0 0; font-size: 13px; color: #1e3a8a;">Notre responsable du recrutement va vous contacter sur votre WhatsApp (<strong>{whatsapp}</strong>) afin de fixer une date et une heure d'entretien.</p>
    </div>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous vous remercions de votre enthousiasme et nous réjouissons de cet échange.</p>
    <p style="color: #2563eb; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
</div>""",
                variables="full_name, job_title, whatsapp"
            ),
            EmailTemplate(
                key="recruitment_accepted",
                name="Candidature Acceptée",
                subject="Félicitations ! Votre candidature est acceptée chez CVisual",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #16a34a; text-align: center; font-size: 22px; margin-bottom: 15px;">Bienvenue chez CVisual Agency ! 🎉</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">C'est avec un immense plaisir que nous vous informons que votre candidature pour le poste de <strong>{job_title}</strong> a été **acceptée** !</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Votre dynamisme, vos compétences et vos réponses à nos questions ont convaincu toute notre équipe. Nous sommes persuadés que vous apporterez une grande valeur ajoutée à l'agence.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous sommes impatients de démarrer cette belle aventure professionnelle avec vous.</p>
    <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 15px; border-radius: 0 8px 8px 0; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #166534;"><strong>Intégration :</strong></p>
        <p style="margin: 5px 0 0 0; font-size: 13px; color: #14532d;">Vous recevrez très prochainement un appel et un message WhatsApp complet décrivant les prochaines étapes de votre onboarding.</p>
    </div>
    <p style="color: #16a34a; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
</div>""",
                variables="full_name, job_title"
            ),
            EmailTemplate(
                key="recruitment_rejected",
                name="Candidature Refusée",
                subject="CVisual - Suite donnée à votre candidature",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #dc2626; text-align: center; font-size: 20px; margin-bottom: 15px;">Suite de votre candidature</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous tenons à vous remercier chaleureusement pour l'intérêt que vous portez à CVisual Agency et pour le temps consacré à votre candidature pour le poste de <strong>{job_title}</strong>.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Après examen attentif de votre dossier et de nos besoins actuels, nous avons le regret de vous informer que nous n'avons pas retenu votre candidature.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Cette décision ne remet nullement en cause la qualité de votre parcours ni celle de vos compétences. Nous conservons précieusement vos informations dans notre vivier de talents pour de futures opportunités cohérentes avec votre profil.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous vous souhaitons beaucoup de réussite dans vos projets professionnels futurs.</p>
    <p style="color: #dc2626; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
</div>""",
                variables="full_name, job_title"
            ),
            EmailTemplate(
                key="inquiry_received",
                name="Devis Reçu",
                subject="CVisual - Demande de devis pour {service} bien reçue",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #1e3a8a; text-align: center; font-size: 20px; margin-bottom: 15px;">Merci pour votre demande de projet !</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{first_name} {last_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous avons bien reçu votre demande de devis pour notre service : <strong>{service}</strong>.</p>
    <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #f3f4f6;">
        <p style="margin: 0 0 10px 0; font-size: 14px; color: #111827;"><strong>Votre Message :</strong></p>
        <p style="margin: 0; font-style: italic; color: #4b5563; font-size: 13px; line-height: 1.5;">"{message}"</p>
    </div>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Un de nos conseillers experts va analyser votre cahier des charges afin de vous proposer une estimation chiffrée sur mesure. Vous serez contacté(e) sous 24 à 48 heures ouvrées.</p>
    <p style="color: #1e3a8a; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
</div>""",
                variables="first_name, last_name, service, message"
            ),
            EmailTemplate(
                key="user_registered",
                name="Inscription Utilisateur",
                subject="Bienvenue sur CVisual - Confirmation d'inscription !",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #1e3a8a; text-align: center; font-size: 20px; margin-bottom: 15px;">Bienvenue dans la communauté CVisual ! 🚀</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Nous sommes ravis de vous compter parmi nos membres. Votre compte a été créé avec succès avec l'adresse email : <strong>{email}</strong>.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Vous pouvez désormais vous connecter à notre plateforme pour suivre l'avancement de vos projets, demander des devis rapides ou postuler à nos offres de recrutement actives.</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="https://cvisual.net/pages/admin/login.html" style="background-color: #2563eb; color: #ffffff; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block;">Accéder à mon Espace</a>
    </div>
    <p style="color: #4b5563; line-height: 1.6; font-size: 15px;">Si vous avez la moindre question, n'hésitez pas à solliciter notre service client via notre chat en direct sur le site.</p>
    <p style="color: #1e3a8a; font-weight: bold; margin-top: 20px; font-size: 15px;">L'équipe CVisual Agency</p>
</div>""",
                variables="full_name, email"
            ),
            EmailTemplate(
                key="user_login",
                name="Connexion Utilisateur",
                subject="CVisual - Nouvelle connexion détectée",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 150px; border-radius: 8px;">
    </div>
    <h2 style="color: #1e3a8a; text-align: center; font-size: 18px; margin-bottom: 15px;">Nouvelle Connexion à votre Compte</h2>
    <p style="color: #4b5563; line-height: 1.6; font-size: 14px;">Bonjour <strong>{full_name}</strong>,</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 14px;">Nous avons détecté une nouvelle connexion à votre compte client CVisual le <strong>{login_time}</strong>.</p>
    <p style="color: #4b5563; line-height: 1.6; font-size: 14px; margin-bottom: 20px;">Si vous êtes à l'origine de cette connexion, aucune action supplémentaire n'est requise.</p>
    <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 0 8px 8px 0; margin: 20px 0; font-size: 13px; color: #b45309;">
        <strong>Sécurité :</strong> Si vous ne reconnaissez pas cette activité, veuillez immédiatement modifier votre mot de passe et contacter notre support.
    </div>
    <p style="color: #1e3a8a; font-weight: bold; margin-top: 20px; font-size: 14px;">L'équipe CVisual Security</p>
</div>""",
                variables="full_name, login_time"
            ),
            EmailTemplate(
                key="broadcast",
                name="Diffusion Générale (Newsletter / Broadcast)",
                subject="{subject}",
                body="""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
    <div style="text-align: center; margin-bottom: 25px;">
        <img src="{logo_url}" alt="CVisual Agency" style="max-width: 160px; border-radius: 8px;">
    </div>
    <h2 style="color: #1e3a8a; font-size: 20px; margin-bottom: 20px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">{subject}</h2>
    <div style="color: #374151; line-height: 1.7; font-size: 15px; margin-bottom: 25px;">
        {message}
    </div>
    <div style="text-align: center; margin: 25px 0;">
        <a href="https://cvisual.net" style="background-color: #111827; color: #ffffff; padding: 12px 35px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block; transition: all 0.2s;">Visiter CVisual</a>
    </div>
    <p style="color: #4b5563; font-size: 14px; margin-top: 20px;">Restez connecté(e) avec nous !</p>
    <p style="color: #1e3a8a; font-weight: bold; font-size: 15px;">L'équipe CVisual Agency</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0 15px 0;">
    <p style="text-align: center; font-size: 11px; color: #9ca3af; margin: 0;">Vous recevez cet email car vous êtes inscrit(e) sur la plateforme ou la newsletter CVisual Agency.<br><a href="#" style="color: #9ca3af; text-decoration: underline;">Se désabonner</a></p>
</div>""",
                variables="subject, message"
            )
        ]
        for t in templates:
            db.session.add(t)

        print("Seeding Recruitment Info...")
        # RecruitmentInfo
        rec = RecruitmentInfo(
            job_title='Agent Commercial Mobile',
            job_details='Nous recherchons des agents motivés pour promouvoir nos solutions numériques et services de branding.',
            is_active=True
        )
        db.session.add(rec)

        print("Seeding Services...")
        # Services
        services = [
            Service(title='Design Web & UI/UX', description='Des interfaces modernes et intuitives qui captivent vos utilisateurs.', icon='layout', image='/uploads/placeholder-service.jpg'),
            Service(title='Photographie Pro', description='Sublimez vos produits et votre équipe avec des clichés haute définition.', icon='camera', image='/uploads/placeholder-service.jpg'),
            Service(title='Social Media', description='Gérez votre présence sur les réseaux sociaux avec stratégie et créativité.', icon='share-2', image='/uploads/placeholder-service.jpg')
        ]
        for s in services:
            db.session.add(s)

        print("Seeding News...")
        # News
        news = [
            News(title='CVisual recrute des Agents !', content='Nous cherchons des commerciaux passionnés pour rejoindre notre équipe mobile à Delmas.', type='recrutement', image='/uploads/placeholder-news.jpg'),
            News(title='Nouveau Portfolio en ligne', content='Découvrez nos dernières réalisations pour les entreprises locales.', type='actualite', image='/uploads/placeholder-news.jpg')
        ]
        for n in news:
            db.session.add(n)

        print("Seeding Clients...")
        # Clients
        clients = [
            Client(name='Google', logo='https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'),
            Client(name='Meta', logo='https://upload.wikimedia.org/wikipedia/commons/7/7b/Meta_Platforms_Inc._logo.svg')
        ]
        for c in clients:
            db.session.add(c)

        db.session.commit()
        print("Database successfully initialized and fully seeded with default CVisual data & premium email templates!")

if __name__ == '__main__':
    init_data()
