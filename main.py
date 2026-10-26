import asyncio
from dotenv import load_dotenv
from src.audio.transcriber import AudioTranscriber
from src.agents.workflow import MeetingWorkflow
from src.mcp_client import export_tasks_via_mcp

load_dotenv()

def main():
    audio_path = "data/sample_meeting.mp3"
    
    print("1. Розпізнавання аудіо...")
    transcriber = AudioTranscriber()
    text = transcriber.transcribe(audio_path)

    print("2. Робота мультиагентного графа...")
    workflow = MeetingWorkflow()
    final_state = workflow.run(text)
    
    print("3. Експорт завдань через MCP-протокол...")
    asyncio.run(export_tasks_via_mcp(final_state['action_items']))

if __name__ == "__main__":
    main()