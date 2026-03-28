# 🌐 Influencer Engagement and Sponsorship Coordination Platform

## 📌 Overview
This project is a web-based platform that connects **sponsors** with **influencers** for advertising and promotional campaigns.

It enables sponsors to create campaigns and collaborate with influencers, while influencers can explore opportunities, manage requests, and participate in campaigns.

---

## 🎯 Objective
To streamline influencer marketing by providing a centralized platform for:
- Campaign creation and management
- Influencer discovery
- Ad request handling
- Communication between sponsors and influencers

---

## 🏗️ Tech Stack

- **Backend:** Flask  
- **Frontend:** HTML, Jinja2, Bootstrap  
- **Database:** SQLite  
- **ORM:** Flask-SQLAlchemy  
- **Authentication:** Werkzeug Security  
- **Environment Management:** python-dotenv  

---

## ⚙️ Features

### 👤 User Roles
- **Admin**
- **Sponsor**
- **Influencer**

---

### 🔐 Authentication
- User registration and login
- Password hashing for security
- Role-based access control

---

### 📢 Campaign Management
- Create, edit, delete campaigns
- Public & private campaign visibility
- Assign influencers to campaigns

---

### 🤝 Influencer-Sponsor Interaction
- Influencers can:
  - Apply to campaigns
  - Accept/reject campaign invitations
- Sponsors can:
  - Search influencers by niche
  - Send ad requests

---

### 💼 Ad Request System
- Create, edit, delete ad requests
- Approve/reject requests
- Track request status

---

### 🔍 Search Functionality
- Search influencers by:
  - Name
  - Category
  - Niche
- Search campaigns by keywords

---

### 🛠️ Admin Dashboard
- View platform statistics
- Manage users
- Flag/unflag users
- Delete campaigns and requests

---

### 🧑 Profile Management
- Update profile details
- Upload profile pictures

---

## 🗄️ Database Schema

### Tables:
- **User**
- **Campaign**
- **CampaignInfluencer**
- **AdRequest**

### Relationships:
- One-to-Many → Sponsor → Campaigns  
- Many-to-Many → Campaign ↔ Influencer  
- One-to-Many → Campaign → AdRequests  

---

## 🚀 Installation

```bash
git clone https://github.com/your-username/influencer-platform.git
cd influencer-platform
pip install -r requirements.txt
