from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from rag_engine import RAGEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioIVRHandler:
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
    
    def handle_incoming_call(self) -> str:
        """Generate TwiML for incoming call with welcome message."""
        response = VoiceResponse()
        
        # Welcome message
        response.say(
            "Hello! I'm your AI knowledge assistant. You can ask me questions about the documents in my knowledge base.",
            voice='Polly.Joanna'
        )
        
        # Gather speech input
        gather = Gather(
            input='speech',
            action='/voice/gather',
            speech_timeout='auto',
            language='en-US',
            hints='document, information, summary, explain'
        )
        gather.say(
            "Please speak your question now.",
            voice='Polly.Joanna'
        )
        response.append(gather)
        
        # Fallback if no input
        response.say(
            "I didn't hear anything. Please try calling again. Goodbye!",
            voice='Polly.Joanna'
        )
        response.hangup()
        
        return str(response)
    
    def handle_speech_input(self, speech_result: str) -> str:
        """Process transcribed speech and generate response."""
        logger.info(f"Received speech: {speech_result}")
        
        response = VoiceResponse()
        
        if not speech_result:
            response.say(
                "I didn't catch that. Please try again.",
                voice='Polly.Joanna'
            )
            response.redirect('/voice/incoming')
            return str(response)
        
        try:
            # Query RAG engine
            result = self.rag_engine.query(speech_result)
            answer = result['answer']
            logger.info(f"RAG response: {answer}")
            
            # Speak the answer
            response.say(answer, voice='Polly.Joanna')
            
            # Ask if they want to continue
            gather = Gather(
                input='speech',
                action='/voice/continue',
                speech_timeout='auto',
                language='en-US',
                num_digits=1,
                timeout=3
            )
            gather.say(
                "Would you like to ask another question? Say yes or no.",
                voice='Polly.Joanna'
            )
            response.append(gather)
            
            # Default to ending call
            response.say("Thank you for calling. Goodbye!", voice='Polly.Joanna')
            response.hangup()
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            response.say(
                "I'm sorry, I encountered an error processing your request. Please try again later.",
                voice='Polly.Joanna'
            )
            response.hangup()
        
        return str(response)
    
    def handle_continue(self, speech_result: str) -> str:
        """Handle user's response to continue prompt."""
        logger.info(f"Continue response: {speech_result}")
        
        response = VoiceResponse()
        
        # Check if user wants to continue
        if speech_result and any(word in speech_result.lower() for word in ['yes', 'yeah', 'sure', 'yep']):
            # Restart conversation
            gather = Gather(
                input='speech',
                action='/voice/gather',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say(
                "Great! What would you like to know?",
                voice='Polly.Joanna'
            )
            response.append(gather)
            
            response.say("I didn't hear anything. Goodbye!", voice='Polly.Joanna')
            response.hangup()
        else:
            # End call
            response.say(
                "Thank you for calling. Have a great day!",
                voice='Polly.Joanna'
            )
            response.hangup()
        
        return str(response)
