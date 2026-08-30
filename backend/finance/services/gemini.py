import os
import json
from google import genai
from google.genai import types


class GeminiServiceError(Exception):
    pass


GET_TRANSACTIONS_SCHEMA = types.FunctionDeclaration(
    name='get_transactions',
    description='Retrieve the authenticated user\'s financial transactions with optional filters',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'start_date': types.Schema(
                type=types.Type.STRING,
                description='Start date for filtering transactions (YYYY-MM-DD)',
            ),
            'end_date': types.Schema(
                type=types.Type.STRING,
                description='End date for filtering transactions (YYYY-MM-DD)',
            ),
            'transaction_type': types.Schema(
                type=types.Type.STRING,
                description='Type of transaction to filter by',
                enum=['income', 'expense'],
            ),
            'category': types.Schema(
                type=types.Type.STRING,
                description='Category name to filter by (case-insensitive)',
            ),
            'limit': types.Schema(
                type=types.Type.INTEGER,
                description='Maximum number of transactions to return (default 50, max 100)',
            ),
        },
    ),
)

GET_FINANCIAL_SUMMARY_SCHEMA = types.FunctionDeclaration(
    name='get_financial_summary',
    description='Calculate the authenticated user\'s financial summary including total income, expenses, net balance, and savings rate',
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            'start_date': types.Schema(
                type=types.Type.STRING,
                description='Start date for filtering transactions (YYYY-MM-DD)',
            ),
            'end_date': types.Schema(
                type=types.Type.STRING,
                description='End date for filtering transactions (YYYY-MM-DD)',
            ),
        },
    ),
)

TOOLS = [types.Tool(function_declarations=[GET_TRANSACTIONS_SCHEMA, GET_FINANCIAL_SUMMARY_SCHEMA])]


class GeminiService:
    def __init__(self, client=None):
        if client is not None:
            self.client = client
        else:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                raise GeminiServiceError('GEMINI_API_KEY not configured in environment')
            self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-3.6-flash'

    def send_prompt(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise GeminiServiceError('Prompt cannot be empty')
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )
            if not response.text:
                raise GeminiServiceError('Empty response from Gemini')
            return response.text.strip()
        except Exception as e:
            raise GeminiServiceError(f'Gemini API error: {str(e)}')

    def send_prompt_with_tools(self, prompt: str, user) -> str:
        if not prompt or not prompt.strip():
            raise GeminiServiceError('Prompt cannot be empty')
        if not user or not user.is_authenticated:
            raise GeminiServiceError('Authenticated user required')

        from finance.tools.transactions import get_transactions, get_financial_summary, TransactionToolError

        try:
            contents = [prompt]
            max_iterations = 5

            for _ in range(max_iterations):
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1024,
                        tools=TOOLS,
                    ),
                )

                if not response.candidates:
                    raise GeminiServiceError('No response from Gemini')

                candidate = response.candidates[0]
                if not candidate.content or not candidate.content.parts:
                    raise GeminiServiceError('Empty response from Gemini')

                function_calls = []
                text_parts = []

                for part in candidate.content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                    elif part.text:
                        text_parts.append(part.text)

                if function_calls:
                    contents.append(candidate.content)

                    for func_call in function_calls:
                        if func_call.name == 'get_transactions':
                            args = dict(func_call.args) if func_call.args else {}
                            try:
                                result = get_transactions(user, **args)
                                result_json = json.dumps(result)
                            except TransactionToolError as e:
                                result_json = json.dumps({'error': str(e)})
                            except Exception as e:
                                result_json = json.dumps({'error': f'Tool execution failed: {str(e)}'})

                            contents.append(types.Content(
                                parts=[types.Part.from_function_response(
                                    name='get_transactions',
                                    response={'result': result_json}
                                )]
                            ))
                        elif func_call.name == 'get_financial_summary':
                            args = dict(func_call.args) if func_call.args else {}
                            try:
                                result = get_financial_summary(user, **args)
                                result_json = json.dumps(result)
                            except TransactionToolError as e:
                                result_json = json.dumps({'error': str(e)})
                            except Exception as e:
                                result_json = json.dumps({'error': f'Tool execution failed: {str(e)}'})

                            contents.append(types.Content(
                                parts=[types.Part.from_function_response(
                                    name='get_financial_summary',
                                    response={'result': result_json}
                                )]
                            ))
                        else:
                            contents.append(types.Content(
                                parts=[types.Part.from_function_response(
                                    name=func_call.name,
                                    response={'error': f'Unknown function: {func_call.name}'}
                                )]
                            ))
                else:
                    return ' '.join(text_parts).strip() if text_parts else ''

            raise GeminiServiceError('Max tool iterations reached')

        except Exception as e:
            if isinstance(e, GeminiServiceError):
                raise
            raise GeminiServiceError(f'Gemini API error: {str(e)}')


_gemini_service = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def reset_gemini_service():
    """Reset the cached Gemini service for testing."""
    global _gemini_service
    _gemini_service = None