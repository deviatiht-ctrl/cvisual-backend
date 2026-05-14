from app import app, db, Service, Project, Stat, News, Client, Testimonial
from werkzeug.security import generate_password_hash

def init_data():
    with app.app_context():
        # Clear existing
        db.drop_all()
        db.create_all()

        # Stats
        stats = [
            Stat(key='projects', value='150+'),
            Stat(key='satisfaction', value='100%'),
            Stat(key='years', value='5+'),
            Stat(key='support', value='24/7')
        ]
        db.session.bulk_save_objects(stats)

        # Services
        services = [
            Service(title='Design Web & UI/UX', description='Des interfaces modernes et intuitives qui captivent vos utilisateurs.', icon='layout', features='Mobile Responsive, SEO Optimized, Custom Design'),
            Service(title='Photographie Pro', description='Sublimez vos produits et votre équipe avec des clichés haute définition.', icon='camera', features='Portrait, Produit, Événementiel'),
            Service(title='Social Media', description='Gérez votre présence sur les réseaux sociaux avec stratégie et créativité.', icon='share-2', features='Content Strategy, Ads Management, Community Management')
        ]
        db.session.bulk_save_objects(services)

        # News
        news = [
            News(title='CVisual recrute des Designers !', content='Nous cherchons des talents passionnés par le UI/UX pour rejoindre notre équipe à Delmas.', type='recrutement'),
            News(title='Nouveau Portfolio en ligne', content='Découvrez nos dernières réalisations pour les entreprises locales.', type='actualite')
        ]
        db.session.bulk_save_objects(news)

        db.session.commit()
        print("Database initialized with default data!")

if __name__ == '__main__':
    init_data()
