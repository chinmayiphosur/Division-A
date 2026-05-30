import os
from groq import Groq

def generate_fault_report(fault_row):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY environment variable not set."
        
    client = Groq(api_key=api_key)
    
    prompt = f"""You are a smart city infrastructure analyst writing official fault reports.

Generate a structured fault report for street light {fault_row['node_id']}:

Location: {fault_row['lat']:.5f}, {fault_row['lon']:.5f}
Road Type: {fault_row['road_type']}
Fault Type: {fault_row['fault_type']}
Priority: {fault_row['priority']}
Sensor Readings:
  Voltage: {fault_row['avg_v']:.1f}V (nominal 230V)
  Current: {fault_row['avg_c']:.3f}A
  Power: {fault_row['avg_p']:.1f}W
  Brightness: {fault_row['avg_brightness']:.1f}%
  Power Variation (CoV): {fault_row['cv_p']:.3f}
  On-time ratio: {fault_row['on_ratio']*100:.1f}%

Write a professional fault report with these exact sections:
1. FAULT SUMMARY (2 sentences)
2. TECHNICAL ANALYSIS (3 sentences explaining the sensor readings)
3. RISK ASSESSMENT (1-2 sentences on safety/service impact)
4. RECOMMENDED ACTION (2-3 sentences)

Be specific, professional, and concise."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {str(e)}"
