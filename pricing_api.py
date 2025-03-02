import openai
import requests
import os
import smtplib
from flask import Flask, request, jsonify
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Secure API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SQUARE_LOCATION_ID = os.getenv("SQUARE_LOCATION_ID")
SMTP_SERVER = "smtp.sendgrid.net"
SMTP_PORT = 587

app = Flask(__name__)

### 1️⃣ AI-Based Pricing Calculation for Tint First ###
def get_ai_quote(first_name, last_name, email, phone, vehicle_type, tint_selection, vehicle_details, old_tint):
    if vehicle_type.lower() == "building":
        return "Manual Contact Required"

    prompt = f"""
    You are a pricing expert for **Tint First**, a premium window tinting company located at:
    **6670 Central Pike, Mount Juliet, TN 37122**.

    - **Tint First only uses high-end ceramic tint**, so pricing should reflect **premium service**.
    - Customers expect **exceptional quality and durability**.
    - Consider labor difficulty, window size, and tint removal when applicable.

    Customer Info:
    - Name: {first_name} {last_name}
    - Email: {email}
    - Phone: {phone}

    Vehicle Info:
    - Type: {vehicle_type}
    - Tint Selection: {tint_selection}
    - Car Model: {vehicle_details}
    - Old Tint Removal Needed: {old_tint}

    Generate a **realistic high-end pricing estimate** for this job, formatted as a single dollar amount.
    """

    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a vehicle tint pricing expert for Tint First, a high-end tint shop specializing in ceramic tint."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"].strip().replace("$", "")
    
    except openai.error.OpenAIError as e:
        return f"Error generating quote: {str(e)}"

@app.route('/get-quote', methods=['POST'])
def get_quote():
    data = request.json
    quote_price = get_ai_quote(
        data['Whats Your Name First Name'],
        data['Whats Your Name Last Name'],
        data['Whats Your Email Address'],
        data['Whats Your Phone Number'],
        data['Are You Booking For A Car Or A Building'],
        data['What Part Of Your Car Needs Tint'],
        data['What Car Needs Tint'],
        data['Do You Need Old Tint Removed']
    )

    return jsonify({"quote_price": quote_price})


### 2️⃣ Square Invoice Creation (Only for Automotive Quotes) ###
def create_square_invoice(email, amount_due):
    if amount_due == "Manual Contact Required":
        return {"message": "Manual follow-up required for residential/commercial jobs."}

    url = "https://connect.squareup.com/v2/invoices"
    headers = {
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "invoice": {
            "location_id": SQUARE_LOCATION_ID,
            "primary_recipient": {"customer_email_address": email},
            "line_items": [
                {
                    "name": "Premium Ceramic Window Tinting",
                    "quantity": "1",
                    "base_price_money": {"amount": int(float(amount_due) * 100), "currency": "USD"}
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Square API Error: {str(e)}"}

@app.route('/send-invoice', methods=['POST'])
def send_invoice():
    data = request.json
    invoice = create_square_invoice(data['Whats Your Email Address'], data['quote_price'])
    return jsonify(invoice)


### 3️⃣ Personalized Quote Email (Without Scheduling Link) ###
def send_quote_email(email, first_name, quote_price, invoice_url):
    try:
        if quote_price == "Manual Contact Required":
            body = f"""
            <p>Hi {first_name},</p>

            <p>Thank you for your interest in **Tint First** for your **residential/commercial window tinting**.</p>
            <p>Since every project is unique, our team will personally review your request and reach out to you shortly.</p>

            <p>If you need immediate assistance, feel free to call us at **(Your Business Phone Number).**</p>

            <p>Best,</p>
            <p><strong>Tint First Team</strong></p>
            """
        else:
            body = f"""
            <p>Hi {first_name},</p>

            <p>Thank you for choosing **Tint First**! Your **premium ceramic window tinting quote** is:</p>

            <h2 style="color: #2d89ef;">💰 ${quote_price}</h2>

            <p>To confirm your appointment, please complete your payment here:</p>

            <p><a href="{invoice_url}" style="background: #2d89ef; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Pay Now</a></p>

            <p>Once payment is received, you will receive a separate email with your scheduling link.</p>

            <p>Best,</p>
            <p><strong>Tint First Team</strong></p>
            """

        subject = "Your Tint First Window Tinting Quote"
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = "your-email@example.com"
        msg["To"] = email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login("apikey", SENDGRID_API_KEY)
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")

@app.route('/send-quote-email', methods=['POST'])
def send_quote_email_route():
    data = request.json
    send_quote_email(
        data['Whats Your Email Address'],
        data['Whats Your Name First Name'],
        data['quote_price'],
        data['invoice_url']
    )
    return jsonify({"message": "Quote email sent successfully!"})


### 4️⃣ Separate Email With Calendly Link (Sent After Payment) ###
def send_scheduling_email(email, first_name):
    body = f"""
    <p>Hi {first_name},</p>

    <p>We’ve received your payment! Now it’s time to schedule your window tint installation.</p>

    <p><a href="https://calendly.com/your-scheduling-page">Schedule Your Appointment</a></p>

    <p>Best,</p>
    <p><strong>Tint First Team</strong></p>
    """

@app.route('/send-scheduling-email', methods=['POST'])
def send_scheduling_email_route():
    data = request.json
    send_scheduling_email(data['Whats Your Email Address'], data['Whats Your Name First Name'])
    return jsonify({"message": "Scheduling email sent successfully!"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
