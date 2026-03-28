from flask import Flask, render_template, redirect, url_for, session, jsonify
from flask import request as flask_request
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import uuid
from functools import wraps
from datetime import datetime

#Loading environment variables from a .env file
load_dotenv()

#innitialize Flask application
app = Flask(__name__)
app.secret_key = 'Jeet12345'  #Set a secret key for session management

#Configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform4u.db'  #SQLite database URI
app.config['UPLOAD_FOLDER'] = 'static/profile_pictures'  #Folder to store profile pictures
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create the folder if it does not exist

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)#Unique identifier for each user
    username = db.Column(db.String(80), unique=True, nullable=False)  # Username (must be unique)
    password = db.Column(db.String(120), nullable=False)  # Hashed password
    role = db.Column(db.String(50), nullable=False)  #Role (sponsor, influencer)
    full_name = db.Column(db.String(100), nullable=False)  #Full name of the user
    email = db.Column(db.String(100), nullable=False)#Email address
    bio = db.Column(db.Text, nullable=True)  #Biography
    category = db.Column(db.String(100), nullable=True)  #Category of interest
    niche = db.Column(db.String(100), nullable=True)  # Niche area
    reach = db.Column(db.String(100), nullable=True)  #Reach (followers count)
    industry = db.Column(db.String(100), nullable=True)  # Industry of work
    budget = db.Column(db.String(100), nullable=True)  # Budget for campaigns
    is_flagged = db.Column(db.Boolean, default=False)  #Flagged status (for review)
    profile_picture = db.Column(db.String(255), nullable=True)#Path to profile picture
    is_active = db.Column(db.Boolean, default=True)  # Active status of the user

    # Relationship: Campaigns created by the user (if they are a sponsor)
    campaigns = db.relationship('Campaign', backref='sponsor')

    # Relationship: Campaigns the user is participating in (if they are an influencer)
    influencer_campaigns = db.relationship(
        'Campaign',
        secondary='campaign_influencer',
        backref='influencers'
    )

#Define the Campaign model
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Unique identifier for each campaign
    name = db.Column(db.String(100), nullable=False)  #Name of the campaign
    description = db.Column(db.Text, nullable=True)  # Description of the campaign
    start_date = db.Column(db.Date, nullable=True)  #Start date of the campaign
    end_date = db.Column(db.Date, nullable=True) #end date of the campaign
    budget = db.Column(db.Integer, nullable=True)  #Budget allocated for the campaign
    visibility = db.Column(db.String(50), nullable=False, default='public')  # Visibility status
    goals = db.Column(db.Text, nullable=True)  #Goals of the campaign
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User (sponsor)
    
    #Relationship: CampaignInfluencers associated with the campaign
    campaign_influencers = db.relationship('CampaignInfluencer', backref='campaign')

#Define the CampaignInfluencer model(many-to-many relationship between Campaign and Influencer)
class CampaignInfluencer(db.Model):
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), primary_key=True)  #Foreign key to Campaign
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) # Foreign key to User (influencer)
    status = db.Column(db.String(20), default='Pending') #Status of the campaign for the influencer



#Define the AdRequest model
class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each ad request
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)  #Foreign key to Campaign
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  #Foreign key to User (influencer)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  #Foreign key to User (sponsor)
    messages = db.Column(db.Text, nullable=False)  # Messages related to the ad request
    requirements = db.Column(db.Text, nullable=False)  # Requirements for the ad request
    payment_amount = db.Column(db.Float, nullable=False)# Payment amount for the ad request
    status = db.Column(db.String(20), default='Pending')  # Status of the ad request

    #Relationships to Campaign and Users
    campaign = db.relationship('Campaign', backref='ad_requests')
    influencer = db.relationship('User', foreign_keys=[influencer_id], backref='influencer_requests') #backref creates a reverse relationship
    sponsor = db.relationship('User', foreign_keys=[sponsor_id], backref='sponsor_requests')

    def __repr__(self):
        return f'<AdRequest {self.id}>'

# Create database tables if they do not already exist
with app.app_context():
    # db.drop_all()  #Drop all existing tables
    db.create_all()  #Create tables based on the current model

# Route for the home page
@app.route("/")
def home():
    if 'user' in session:
        user = session['user']
        if 'id' in user:
            # Fetch the user object from the database
            user_from_db = User.query.get(user['id'])
            return render_template("home.html", user=user_from_db)  #Render home page with user info
        else:

            return redirect(url_for('login'))  #Redirect to login if user info is missing
    else:
        return redirect(url_for('login'))  # Redirect to login if no user in session

# Route for login page
@app.route("/login",  methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('home'))  # Redirect to home if already logged in
    user = {'name': '', "password": '', 'role': ''}
    if flask_request.method == "POST":
        username = flask_request.form.get('name')
        password = flask_request.form.get('password')

        # Hardcoded admin credentials
        admin_username = 'admin'
        admin_password = '000'
        if username == admin_username and password == admin_password:
            session['user'] = {'name': username, 'role': 'admin'}
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard

        # Authenticate user using database
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):  # Verify password
            # Convert User object to a dictionary
            session_user = {
                'id': user.id,
                'name': user.full_name,
                'role': user.role,
                'profile_picture': user.profile_picture  # Add profile_picture to session
            }
            session['user'] = session_user  # Store user info in session
            return redirect(url_for('home'))  # Redirect to home page
        else:
            error = 'Invalid username or password'
            return render_template("login.html", error=error, user=user)  # Render login page with error message
    else:
        return render_template("login.html", user=user)  # Render login page for GET request

# Route for registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    user = {'name':'', 'password': '', 'role': ''}
    if flask_request.method == "POST":
        username = flask_request.form.get('username')
        password = flask_request.form.get('password')
        confirm_password = flask_request.form.get('confirm-password')
        full_name = flask_request.form.get('full-name')
        email = flask_request.form.get('email')
        role = flask_request.form.get('role')
        bio = flask_request.form.get('bio')
        category = flask_request.form.get('category')
        niche = flask_request.form.get('niche')
        reach = flask_request.form.get('reach')
        industry = flask_request.form.get('industry')
        budget = flask_request.form.get('budget')

        #Checking for existing username
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("register.html", user=user, error="Username already exists")  #error if username exists

        # Check if passwords match
        if password != confirm_password:
            return render_template("register.html", user=user, error="Passwords do not match")  # Error if passwords do not match

        # Register user in database
        hashed_password = generate_password_hash(password)  # Hash the password
        new_user = User(username=username, password=hashed_password, role=role, full_name=full_name, email=email, bio=bio, category=category, niche=niche, reach=reach, industry=industry, budget=budget)
        db.session.add(new_user)
        db.session.commit()
        session['user'] = {'name': username, 'role': role, 'id': new_user.id, 'profile_picture': new_user.profile_picture}
        return redirect(url_for('home'))  #Redirect to home page after registration
    return render_template("register.html", user=user)  #render registration page for GET request

#Route for logout
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)  #remove user from session
    return redirect(url_for('login'))  #Redirect to login page


def is_flagged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' in session:
            user_id = session['user']['id']  #Get the user ID from the session
            user = User.query.get(user_id)  # Fetch the User object from the database
            if user and user.is_flagged:  #Check if the user is flagged
                return redirect(url_for('home'))  #Redirect to home if flagged
        return func(*args, **kwargs)  # Otherwise, proceed with the function
    return wrapper

#Route for influencer campaign management
@app.route('/influencer_campaigns', methods=['GET'])
@is_flagged
def influencer_campaigns():
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        #Fetchingg private campaigns where the influencer is either Approved or Pending
        campaigns = (
            db.session.query(Campaign)
            .join(CampaignInfluencer, Campaign.id == CampaignInfluencer.campaign_id)
            .filter(CampaignInfluencer.influencer_id == user['id'])
            .all()
        )

        #Fetch ad requests related to the influencer's campaigns
        ad_requests = AdRequest.query.filter_by(influencer_id=user['id']).all()

        return render_template("influencer_campaigns.html", campaigns=campaigns, user=user, ad_requests=ad_requests)  # Render influencer campaigns page
    else:
        return redirect(url_for('login'))  #Redirect to login if user is not an influencer


@app.route('/accept_campaign/<int:campaign_id>', methods=['POST'])
@is_flagged
def accept_campaign(campaign_id):
    # Check if user is logged in and is an influencer
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Find the CampaignInfluencer entry for the specified campaign and the logged-in influencer
        campaign_influencer = CampaignInfluencer.query.filter_by(campaign_id=campaign_id, influencer_id=user['id']).first()
        if campaign_influencer:
            campaign_influencer.status = 'Approved'  # Update the status to 'Approved'
            db.session.commit()  # Commit changes to the database
        return redirect(url_for('influencer_campaigns'))  # Redirect to the influencer's campaign page
    else:
        return redirect(url_for('login'))  # Redirect to login if the user is not an influencer

@app.route('/reject_campaign/<int:campaign_id>', methods=['POST'])
@is_flagged
def reject_campaign(campaign_id):
    # Check if user is logged in and is an influencer
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Find the CampaignInfluencer entry for the specified campaign and the logged-in influencer
        campaign_influencer = CampaignInfluencer.query.filter_by(campaign_id=campaign_id, influencer_id=user['id']).first()
        if campaign_influencer:
            campaign_influencer.status = 'Rejected'  # Update the status to 'Rejected'
            db.session.commit()  # Commit changes to the database
        return redirect(url_for('influencer_campaigns'))  # Redirect to the influencer's campaign page
    else:
        return redirect(url_for('login'))  # Redirect to login if the user is not an influencer

@app.route('/update_profile_inf', methods=['POST'])
@is_flagged
def update_profile_inf():
    # Check if user is logged in and is an influencer
    if 'user' in session and session['user']['role'] == 'influencer':
        user_id = flask_request.form.get('user_id')
        user = User.query.get_or_404(user_id)  # Fetch user by ID, or return 404 if not found
        # Update user profile information from form data
        user.full_name = flask_request.form.get('full-name')
        user.email = flask_request.form.get('email')
        user.bio = flask_request.form.get('bio')
        user.category = flask_request.form.get('category')
        user.niche = flask_request.form.get('niche')
        user.reach = flask_request.form.get('reach')
        db.session.commit()  # Commit changes to the database
        # Update session with new user information
        session['user']['full_name'] = user.full_name
        session['user']['email'] = user.email
        session['user']['bio'] = user.bio
        session['user']['category'] = user.category
        session['user']['niche'] = user.niche
        session['user']['reach'] = user.reach

        return redirect(url_for('home'))  # Redirect to home page
    else:
        return redirect(url_for('login'))  # Redirect to login if the user is not an influencer

@app.route('/upload_profile_picture', methods=['POST'])
@is_flagged
def upload_profile_picture():
    # Check if user is logged in and is an influencer
    if 'user' in session and session['user']['role'] == 'influencer':
        user_id = session['user']['id']
        user = User.query.get_or_404(user_id)  # Fetch user by ID, or return 404 if not found
        if 'profile_picture' in flask_request.files:
            file = flask_request.files['profile_picture']
            if file.filename != '':
                filename = secure_filename(file.filename)  # Secure the file name
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save the file
                user.profile_picture = filename  # Update the profile picture filename in the database
                db.session.commit()  # Commit changes to the database
                session['user']['profile_picture'] = user.profile_picture  # Update session with new profile picture
        
        return redirect(url_for('home'))  # Redirect to home page
    else:
        return redirect(url_for('login'))  # Redirect to login if the user is not an influencer

@app.route('/update_profile_sp', methods=['POST'])
@is_flagged
def update_profile_sp():
    user_id = flask_request.form.get('user_id')
    full_name = flask_request.form.get('full-name')
    email = flask_request.form.get('email')
    bio = flask_request.form.get('bio')
    industry = flask_request.form.get('industry')
    budget = flask_request.form.get('budget')

    user = User.query.get(user_id)  # Fetch user by ID
    if user:
        # Update user profile information from form data
        user.full_name = full_name
        user.email = email
        user.bio = bio
        user.industry = industry
        user.budget = budget
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('home'))  # Redirect to home page
    else:
        return "User not found", 404  # Return a 404 error if the user doesn't exist

@app.route('/upload_profile_picture_sp', methods=['POST'])
@is_flagged
def upload_profile_picture_sp():
    user_id = flask_request.form.get('user_id')  # Get user_id from the form
    user = User.query.get(user_id)  # Fetch user by ID

    if user:  # Check if the user exists
        if 'profile_picture' in flask_request.files:
            profile_picture = flask_request.files['profile_picture']
            if profile_picture.filename != '':
                filename = str(uuid.uuid4()) + '_' + profile_picture.filename  # Create a unique filename
                profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save the file
                user.profile_picture = filename  # Update the profile picture filename in the database
                db.session.commit()  # Commit changes to the database
        return redirect(url_for('home'))  # Redirect to home page
    else:
        return "User not found", 404  # Return a 404 error if the user doesn't exist


# Route to search for influencers
@app.route('/search_influencers', methods=['GET', 'POST'])
@is_flagged
def search_influencers():
    # Check if the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Check the HTTP request method
        if flask_request.method == 'POST':
            search_term = flask_request.form.get('search_term')  # Get the search term from the form
            niche = flask_request.form.get('niche')  # Get the niche from the form

            if search_term or niche:
                # If a search term or niche is provided, filter influencers
                query = User.query.filter_by(role='influencer')
                if search_term:
                    # Filter by full name, niche, or category if search term is provided
                    query = query.filter(
                        (User.full_name.like(f'%{search_term}%')) |
                        (User.niche.like(f'%{search_term}%')) |
                        (User.category.like(f'%{search_term}%'))
                    )
                if niche:
                    # Filter by niche if provided
                    query = query.filter_by(niche=niche)
                influencers = query.all()  # Retrieve the filtered list of influencers
                # Render the search results template with the list of influencers
                return render_template('search_influencers.html', influencers=influencers, user=user)
            else:
                # If no search term or niche is provided, show all influencers
                influencers = User.query.filter_by(role='influencer').all()
                return render_template('search_influencers.html', influencers=influencers, user=user)
        else:
            # If the request method is GET, just render the search template
            return render_template('search_influencers.html', user=user)
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

from datetime import datetime

# Route to get a list of unique niches
@app.route('/get_niches')
def get_niches():
    # Query to get distinct niches for influencers
    niches = db.session.query(User.niche).distinct().filter(User.role == 'influencer').all()
    # Convert the result to a list of niche strings and return as JSON
    return jsonify([niche[0] for niche in niches])

# Route to get influencers by a specific niche
@app.route('/get_influencers_by_niche/<niche>')
def get_influencers_by_niche(niche):
    # Query to get influencers filtered by the given niche
    influencers = User.query.filter_by(role='influencer', niche=niche).all()
    # Convert the list of influencers to a list of dictionaries with id and full name
    return jsonify([{'id': influencer.id, 'full_name': influencer.full_name} for influencer in influencers])

# Route to create a new campaign
@app.route('/create_campaign', methods=['GET', 'POST'])
@is_flagged
def create_campaign():
    # Check if the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Check the HTTP request method
        if flask_request.method == 'POST':
            campaign_name = flask_request.form.get('campaign_name')
            description = flask_request.form.get('description')
            start_date_str = flask_request.form.get('start_date')
            end_date_str = flask_request.form.get('end_date')
            budget = flask_request.form.get('budget')
            visibility = flask_request.form.get('visibility')
            goals = flask_request.form.get('goals')
            niche = flask_request.form.get('niche')
            selected_influencers = flask_request.form.getlist('influencer_ids[]')  # Get list of selected influencer IDs

            # Convert start and end dates from strings to date objects
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Create a new campaign instance
            new_campaign = Campaign(
                name=campaign_name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                visibility=visibility,
                goals=goals,
                sponsor_id=user['id']
            )
            db.session.add(new_campaign)  # Add the campaign to the session
            db.session.commit()  # Commit to save and get the new campaign ID

            # Insert each selected influencer into the CampaignInfluencer table
            for influencer_id in selected_influencers:
                campaign_influencer = CampaignInfluencer(
                    campaign_id=new_campaign.id,
                    influencer_id=influencer_id
                )
                db.session.add(campaign_influencer)
            db.session.commit()  # Commit to save the relationships

            # Redirect to the sponsor's list of campaigns
            return redirect(url_for('my_campaigns'))
        else:
            # If the request method is GET, get the list of influencers and render the campaign creation template
            influencers = User.query.filter_by(role='influencer').all()
            return render_template("create_campaign.html", user=user, influencers=influencers)
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

# Route to edit an ad request
@app.route('/edit_ad_request/<int:request_id>', methods=['GET', 'POST'])
@is_flagged
def edit_ad_request(request_id):
    # Check if the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Fetch the ad request by ID or return 404 if not found
        request = AdRequest.query.get_or_404(request_id)
        # Check if the request belongs to the logged-in influencer
        if request.influencer_id != user['id']:
            
            return redirect(url_for('request_list'))
        if flask_request.method == 'POST':
            # Update the ad request details with form data
            request.messages = flask_request.form.get('messages')
            request.requirements = flask_request.form.get('requirements')
            request.payment_amount = flask_request.form.get('payment_amount')
            db.session.commit()  # Commit changes to the database
  
            return redirect(url_for('request_list'))
        # Render the template for editing the ad request
        return render_template("edit_ad_request.html", request=request, user=user)
    else:
        # Redirect to login if the user is not an influencer
        return redirect(url_for('login'))

    # Route to delete an ad request
@app.route('/delete_ad_request/<int:request_id>', methods=['POST'])
@is_flagged
def delete_ad_request(request_id):
    # Check if the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Fetch the ad request by ID or return 404 if not found
        ad_request = AdRequest.query.get_or_404(request_id)
        # Check if the request belongs to the logged-in influencer
        if ad_request.influencer_id != user['id']:
            return redirect(url_for('request_list'))
        # Delete the ad request
        db.session.delete(ad_request)
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('request_list'))
    else:
        # Redirect to login if the user is not an influencer
        return redirect(url_for('login'))

# Route to list ad requests for an influencer
@app.route('/request_list', methods=['GET'])
@is_flagged
def request_list():
    # Check if the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user'].get('role') == 'influencer' and 'id' in session['user']:
        user = session['user']
        # Query to get all ad requests for the logged-in influencer
        requests = AdRequest.query.filter_by(influencer_id=user['id']).all()
        # Render the template with the list of ad requests
        return render_template("request_list.html", requests=requests, user=user)
    else:
        return redirect(url_for('login'))


# Route to submit an ad request
@app.route('/ad_request', methods=['POST']) # Route to submit ad requests
@is_flagged
def ad_request():
    if 'user' in session:     # Checkin if the user is logged in
        user = session['user']
        request_data = flask_request.get_json()  # Get JSON data from the request
        # Process the ad request in the database
        return 'Ad request submitted'
    else:
        return redirect(url_for('login'))  

# Route for the admin dashboard
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Check if the user is logged in and has the role of 'admin'
    if 'user' in session and session['user']['role'] == 'admin':
        user = session['user']
        # Fetch data for the admin dashboard
        active_users = User.query.count()  # Count all users
        influencers = User.query.filter_by(role='influencer').count()  # Count all influencers
        sponsors = User.query.filter_by(role='sponsor').count()  # Count all sponsors
        campaigns = Campaign.query.all()  # Get all campaigns
        ad_requests = AdRequest.query.all()  # Get all ad requests
        flagged_users = User.query.filter_by(is_flagged=True).all()  # Get all flagged users
        public_campaigns = Campaign.query.filter_by(visibility='public').count()  # Count public campaigns
        private_campaigns = Campaign.query.filter_by(visibility='private').count()  # Count private campaigns
        pending_requests = AdRequest.query.filter_by(status='Pending').count()  # Count pending requests
        approved_requests = AdRequest.query.filter_by(status='Approved').count()  # Count approved requests
        rejected_requests = AdRequest.query.filter_by(status='Rejected').count()  # Count rejected requests
        all_users = User.query.all()  # Get all users
        influencers_list = User.query.filter_by(role='influencer').all()  # Get list of all influencers
        sponsors_list = User.query.filter_by(role='sponsor').all()  # Get list of all sponsors

        # Render the admin dashboard template with all the fetched data
        return render_template("admin_dashboard.html", 
                               user=user, 
                               campaigns=campaigns, 
                               ad_requests=ad_requests, 
                               flagged_users=flagged_users,
                               active_users=active_users,
                               influencers=influencers,
                               sponsors=sponsors,
                               public_campaigns=public_campaigns,
                               private_campaigns=private_campaigns,
                               pending_requests=pending_requests,
                               approved_requests=approved_requests,
                               rejected_requests=rejected_requests,
                               all_users=all_users,
                               influencers_list=influencers_list,
                               sponsors_list=sponsors_list)
    else:
        return redirect(url_for('login'))

# Route to delete a campaign
@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    # Check if the user is logged in and has the role of 'admin'
    if 'user' in session and session['user']['role'] == 'admin':
        user = session['user']
        # Fetch the campaign by ID or return 404 if not found
        campaign = Campaign.query.get_or_404(campaign_id)
        # Delete related CampaignInfluencer entries
        while len(campaign.campaign_influencers) > 0:
            c = campaign.campaign_influencers[0]
            db.session.delete(c)
            db.session.commit()
        
        # Delete the campaign
        db.session.delete(campaign)
        # Delete related ad requests
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
        for request in ad_requests:
            db.session.delete(request)
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('login'))



@app.route('/delete_request/<int:request_id>', methods=['POST'])
def delete_request(request_id):
    # Ensure the user is logged in and has admin role
    if 'user' in session and session['user']['role'] == 'admin':
        user = session['user']
        # Fetch the ad request by ID or return 404 if not found
        ad_request = AdRequest.query.get_or_404(request_id)
        db.session.delete(ad_request)  # Delete the ad request
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
    else:
        return redirect(url_for('login'))

@app.route('/flag_user/<int:user_id>', methods=['POST'])
def flag_user(user_id):
    # Ensure the user is logged in and has admin role
    if 'user' in session and session['user']['role'] == 'admin':
        user = session['user']
        # Fetch the user by ID or return 404 if not found
        user_to_flag = User.query.get_or_404(user_id)
        user_to_flag.is_flagged = True  # Set the user as flagged
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
    else:
        return redirect(url_for('login'))

@app.route('/unflag_user/<int:user_id>', methods=['POST'])
def unflag_user(user_id):
    # Ensure the user is logged in and has admin role
    if 'user' in session and session['user']['role'] == 'admin':
        user = session['user']
        # Fetch the user by ID or return 404 if not found
        user_to_unflag = User.query.get_or_404(user_id)
        user_to_unflag.is_flagged = False  # Remove the flagged status
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
    else:
        return redirect(url_for('login'))


@app.route('/send_ad_request/<int:campaign_id>/<int:influencer_id>', methods=['GET', 'POST'])
@is_flagged
def send_ad_request(campaign_id, influencer_id):
    # Ensure the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']  # The user object
        # Fetch the campaign by ID or return 404 if not found
        campaign = Campaign.query.get_or_404(campaign_id)
        if flask_request.method == 'POST':
            # Get data from the form
            messages = flask_request.form.get('messages')
            requirements = flask_request.form.get('requirements')
            payment_amount = flask_request.form.get('payment_amount')

            # Create a new AdRequest object
            new_request = AdRequest(
                campaign_id=campaign_id,
                influencer_id=user['id'],
                sponsor_id=campaign.sponsor_id,  # Get the sponsor ID from the campaign
                messages=messages,
                requirements=requirements,
                payment_amount=payment_amount
            )

            # Add the request to the database
            db.session.add(new_request)
            db.session.commit()  # Commit changes to the database

            return redirect(url_for('home'))  # Redirect to the home page
        else:
            return render_template('create_ad_request.html', campaign=campaign, user=user)  # Render the ad request form
    else:
        return redirect(url_for('login'))


@app.route('/my_campaigns', methods=['GET'])
@is_flagged
def my_campaigns():
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch all campaigns created by the sponsor
        campaigns = Campaign.query.filter_by(sponsor_id=user['id']).all()
        return render_template("my_campaigns.html", campaigns=campaigns, user=user)  # Render the sponsor's campaigns
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

@app.route('/my_private_campaigns', methods=['GET'])
@is_flagged
def my_private_campaigns():
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch private campaigns with pending status and influencer names
        campaigns = (
            db.session.query(Campaign, User.full_name)
            .select_from(Campaign)
            .join(CampaignInfluencer, Campaign.id == CampaignInfluencer.campaign_id)
            .outerjoin(User, CampaignInfluencer.influencer_id == User.id)
            .filter(Campaign.sponsor_id == user['id'], Campaign.visibility == 'private')
            .all()
        )
        return render_template("private_campaigns.html", campaigns=campaigns, user=user)  # Render the private campaigns
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

@app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@is_flagged
def edit_campaign(campaign_id):
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch the campaign by ID or return 404 if not found
        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.sponsor_id != user['id']:
            return redirect(url_for('my_campaigns'))
        if flask_request.method == 'POST':
            # Update campaign details
            campaign.name = flask_request.form.get('campaign_name')
            campaign.description = flask_request.form.get('description')
            start_date_str = flask_request.form.get('start_date')
            end_date_str = flask_request.form.get('end_date')
            campaign.budget = flask_request.form.get('budget')
            campaign.visibility = flask_request.form.get('visibility')
            campaign.goals = flask_request.form.get('goals')

            # Convert string dates to datetime.date objects
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            campaign.start_date = start_date
            campaign.end_date = end_date

            db.session.commit()  # Commit changes to the database
            return redirect(url_for('my_campaigns'))  # Redirect to the sponsor's campaigns
        return render_template("edit_campaign.html", campaign=campaign, user=user)  # Render the edit campaign form
    else:
        return redirect(url_for('login'))

@app.route('/delete_campaign_sponsor/<int:campaign_id>', methods=['POST'])
@is_flagged
def delete_campaign_sponsor(campaign_id):
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch the campaign by ID or return 404 if not found
        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.sponsor_id != user['id']:
    
            return redirect(url_for('my_campaigns'))

        # Delete associated CampaignInfluencer entries
        campaign_influencers = CampaignInfluencer.query.filter_by(campaign_id=campaign_id).all()
        for campaign_influencer in campaign_influencers:
            db.session.delete(campaign_influencer)

        # Delete associated AdRequests
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
        for request in ad_requests:
            db.session.delete(request)

        db.session.delete(campaign)  # Delete the campaign
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('my_campaigns'))  # Redirect to the sponsor's campaigns
    else:
        return redirect(url_for('login'))




@app.route('/search_campaigns', methods=['GET', 'POST'])
@is_flagged
def search_campaigns():
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        if flask_request.method == 'POST':  # Handle search button click
            search_term = flask_request.form.get('search_term')
            if search_term:
                # Search for public campaigns based on the search term
                campaigns = Campaign.query.filter(
                    Campaign.name.like(f'%{search_term}%') |  # Search by campaign name
                    Campaign.description.like(f'%{search_term}%')  # Search by campaign description
                ).filter_by(visibility='public').all()  # Filter for public campaigns
                return render_template("search_campaigns.html", campaigns=campaigns, user=user)
            else:
                # Show all public campaigns if no search term is provided
                campaigns = Campaign.query.filter_by(visibility='public').all()
                return render_template("search_campaigns.html", campaigns=campaigns, user=user)
        else:  # Show the search form initially
            return render_template("search_campaigns.html", user=user)
    else:
        return redirect(url_for('login'))


# ... (rest of your app.py code)

@app.route('/influencer_campaigns_public', methods=['GET'])
@is_flagged
def influencer_campaigns_public():
    # Ensure the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Fetch all campaigns that are marked as 'public'
        campaigns = Campaign.query.filter_by(visibility='public').all()
        # Render the template to show the list of public campaigns
        return render_template("request_list.html", campaigns=campaigns, user=user)
    else:
        # Redirect to login if the user is not an influencer
        return redirect(url_for('login'))

@app.route('/apply_for_campaign/<int:campaign_id>', methods=['POST'])
@is_flagged
def apply_for_campaign(campaign_id):
    # Ensure the user is logged in and has the role of 'influencer'
    if 'user' in session and session['user']['role'] == 'influencer':
        user = session['user']
        # Fetch the campaign by ID or return 404 if not found
        campaign = Campaign.query.get_or_404(campaign_id)
        # Add the current influencer to the list of influencers for the campaign
        campaign.influencers.append(user)
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('influencer_campaigns_public'))  # Redirect back to the list of public campaigns
    else:
        # Redirect to login if the user is not an influencer
        return redirect(url_for('login'))

@app.route('/view_ad_requests')
@is_flagged
def view_ad_requests():
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        sponsor_id = session['user']['id']  # Get the current sponsor's ID from the session
        # Fetch all ad requests where the sponsor is the one who requested it
        requests = AdRequest.query.filter_by(sponsor_id=sponsor_id).all()
        # Render the template to show the list of ad requests
        return render_template('view_ad_requests.html', requests=requests)
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

@app.route('/approve_request/<int:request_id>', methods=['POST'])
@is_flagged
def approve_request(request_id):
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch the ad request by ID or return 404 if not found
        ad_request = AdRequest.query.get_or_404(request_id)
        ad_request.status = 'Approved'  # Update the request status to 'Approved'
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('view_ad_requests'))  # Redirect to the list of ad requests
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))

@app.route('/reject_request/<int:request_id>', methods=['POST'])
@is_flagged
def reject_request(request_id):
    # Ensure the user is logged in and has the role of 'sponsor'
    if 'user' in session and session['user']['role'] == 'sponsor':
        user = session['user']
        # Fetch the ad request by ID or return 404 if not found
        ad_request = AdRequest.query.get_or_404(request_id)
        ad_request.status = 'Rejected'  # Update the request status to 'Rejected'
        db.session.commit()  # Commit changes to the database
        return redirect(url_for('view_ad_requests'))  # Redirect to the list of ad requests
    else:
        # Redirect to login if the user is not a sponsor
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)  # Run the app in debug mode for development
