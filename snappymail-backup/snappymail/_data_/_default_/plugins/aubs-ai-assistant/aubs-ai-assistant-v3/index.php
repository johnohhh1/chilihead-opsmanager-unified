<?php

/**
 * AUBS AI Assistant - v3.8.0
 * Now fetches FULL email bodies, not just previews
 */

class AubsAiAssistantPlugin extends \RainLoop\Plugins\AbstractPlugin
{
    const
        NAME = 'AUBS AI Assistant',
        VERSION = '3.8.0',
        CATEGORY = 'AI',
        DESCRIPTION = 'AI-powered email intelligence for Chili\'s #605 operations.';

    public function Init(): void
    {
        $this->addJs('js/aubs.js?v=3.8.0');
        $this->addCss('css/aubs.css');
        
        $this->addJsonHook('AubsAnalyze', 'DoAubsAnalyze');
        $this->addJsonHook('AubsGetConfig', 'DoAubsGetConfig');
        $this->addJsonHook('AubsTestConnection', 'DoAubsTestConnection');
        $this->addJsonHook('AubsFetchMessages', 'DoAubsFetchMessages');
    }

    protected function configMapping(): array
    {
        return [
            \RainLoop\Plugins\Property::NewInstance('api_endpoint')
                ->SetLabel('Ollama API Endpoint')
                ->SetType(\RainLoop\Enumerations\PluginPropertyType::STRING)
                ->SetDefaultValue('http://host.docker.internal:11434'),
            
            \RainLoop\Plugins\Property::NewInstance('model_name')
                ->SetLabel('Model Name')
                ->SetType(\RainLoop\Enumerations\PluginPropertyType::STRING)
                ->SetDefaultValue('gpt-oss:120b-cloud'),
            
            \RainLoop\Plugins\Property::NewInstance('allowed_domains')
                ->SetLabel('Work Email Domains (comma-separated)')
                ->SetType(\RainLoop\Enumerations\PluginPropertyType::STRING)
                ->SetDefaultValue('brinker.com,chilis.com,hotshedules.co'),
        ];
    }

    public function DoAubsGetConfig(): array
    {
        return $this->jsonResponse(__FUNCTION__, [
            'endpoint' => $this->Config()->Get('plugin', 'api_endpoint', 'http://host.docker.internal:11434'),
            'model' => $this->Config()->Get('plugin', 'model_name', 'gpt-oss:120b-cloud'),
            'domains' => $this->Config()->Get('plugin', 'allowed_domains', 'brinker.com,chilis.com,hotshedules.co'),
        ]);
    }

    public function DoAubsTestConnection(): array
    {
        $endpoint = $this->Config()->Get('plugin', 'api_endpoint', 'http://host.docker.internal:11434');
        $url = rtrim($endpoint, '/') . '/api/tags';
        
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 5,
            CURLOPT_CONNECTTIMEOUT => 5,
        ]);
        
        $response = curl_exec($ch);
        $error = curl_error($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($error) {
            return $this->jsonResponse(__FUNCTION__, [
                'success' => false,
                'error' => "Connection failed: {$error}",
                'endpoint' => $endpoint
            ]);
        }
        
        $data = json_decode($response, true);
        $models = [];
        if (isset($data['models'])) {
            foreach ($data['models'] as $m) {
                $models[] = $m['name'] ?? 'unknown';
            }
        }
        
        return $this->jsonResponse(__FUNCTION__, [
            'success' => $httpCode === 200,
            'httpCode' => $httpCode,
            'endpoint' => $endpoint,
            'modelCount' => count($models),
            'models' => array_slice($models, 0, 10)
        ]);
    }

    /**
     * Fetch full message bodies for given UIDs
     * This is the key - we fetch FULL content, not just previews
     */
    public function DoAubsFetchMessages(): array
    {
        $aUids = $this->jsonParam('uids', []);
        $sFolder = $this->jsonParam('folder', 'INBOX');
        
        if (empty($aUids)) {
            return $this->jsonResponse(__FUNCTION__, ['error' => 'No UIDs provided', 'messages' => []]);
        }
        
        try {
            $oAccount = $this->Manager()->Actions()->GetAccount();
            if (!$oAccount) {
                return $this->jsonResponse(__FUNCTION__, ['error' => 'No account', 'messages' => []]);
            }
            
            $oMailClient = $this->Manager()->Actions()->MailClient();
            if (!$oMailClient) {
                return $this->jsonResponse(__FUNCTION__, ['error' => 'No mail client', 'messages' => []]);
            }
            
            $messages = [];
            
            foreach ($aUids as $uid) {
                try {
                    // Fetch message with body
                    $oMessage = $oMailClient->Message($sFolder, (int)$uid, true, null);
                    
                    if ($oMessage) {
                        $messages[] = [
                            'uid' => $uid,
                            'from' => $oMessage->From() ? $oMessage->From()->ToString() : '',
                            'to' => $oMessage->To() ? $oMessage->To()->ToString() : '',
                            'subject' => $oMessage->Subject(),
                            'date' => $oMessage->DateTimeStampInUTC(),
                            'body' => $oMessage->Plain() ?: strip_tags($oMessage->Html() ?: ''),
                            'hasBody' => true
                        ];
                    }
                } catch (\Throwable $e) {
                    // Skip individual message errors
                    $messages[] = [
                        'uid' => $uid,
                        'error' => $e->getMessage(),
                        'hasBody' => false
                    ];
                }
            }
            
            return $this->jsonResponse(__FUNCTION__, [
                'success' => true,
                'folder' => $sFolder,
                'count' => count($messages),
                'messages' => $messages
            ]);
            
        } catch (\Throwable $e) {
            return $this->jsonResponse(__FUNCTION__, [
                'error' => $e->getMessage(),
                'messages' => []
            ]);
        }
    }

    public function DoAubsAnalyze(): array
    {
        $sEmail = $this->jsonParam('email', '');
        $sAction = $this->jsonParam('action', 'analyze');
        
        if (empty($sEmail)) {
            return $this->jsonResponse(__FUNCTION__, ['error' => 'No email content provided']);
        }
        
        $endpoint = $this->Config()->Get('plugin', 'api_endpoint', 'http://host.docker.internal:11434');
        $model = $this->Config()->Get('plugin', 'model_name', 'gpt-oss:120b-cloud');
        
        $result = $this->callOllama($endpoint, $model, $sEmail);
        
        return $this->jsonResponse(__FUNCTION__, [
            'success' => !empty($result) && strpos($result, 'Error:') !== 0,
            'response' => $result,
            'model' => $model,
            'endpoint' => $endpoint
        ]);
    }

    private function getSystemPrompt(): string
    {
        $currentDate = date('l, F j, Y');
        $currentTime = date('g:i A') . ' ET';
        
        return <<<PROMPT
You are AUBS (Auburn Hills Assistant) - John's operations AI for Chili's #605.

PERSONALITY:
- Supportive partner focused on making John's job easier
- Clear and direct without being preachy or condescending
- Helpful problem-solver, not a lecturer
- Respects that John knows his team and business
- Focuses on facts and solutions, not explanations of why things matter

COMMUNICATION STYLE:
- State the facts clearly
- Provide specific details (who, what, when, where)
- Suggest solutions when helpful
- Skip the lectures about why something is important
- Trust John to prioritize and make decisions

EXAMPLES OF GOOD vs BAD:
✓ "Hannah's pay card failed - she hasn't been paid in 48 hours. Payroll: 555-0123"
✗ "Real talk, John. This is about recordkeeping and could lead to bigger headaches..."

✓ "Blake called off for tonight 5-10pm. Sarah and Mike are available."
✗ "Here's the deal, you're in the weeds on coverage..."

✓ "P5 schedule due Friday 5pm. Takes about 30 minutes."
✗ "Let's knock this out before it becomes a problem..."

CRITICAL CONTEXT:
- Location: Auburn Hills, MI (America/Detroit timezone)
- Store: Chili's #605
- Current Date: {$currentDate}
- Current Time: {$currentTime}
- Your role: Extract ONLY actionable items from emails

SCOPE & PRIORITY:
1. HotSchedules/911: Coverage issues, call-offs, no-shows (URGENT)
2. Brinker/Leadership: Deadlines, reports, schedule submissions
3. Vendors/Alerts: Securitas, Cintas, Oracle, Fourth
4. Everything else

EXTRACTION REQUIREMENTS:

For 911/Emergency Items:
- WHO called off/didn't show (name if stated in email)
- WHEN exactly (shift date/time)
- COVERAGE STATUS (gaps remaining)
- ACTION REQUIRED (specific steps)

For Deadlines/Deliverables:
- WHAT exactly is due (be specific)
- WHEN due (actual date if stated)
- SUBMISSION METHOD (where/how if stated)

For Action Items:
- SPECIFIC ACTION (not vague)
- WHO needs to do it (only if stated - otherwise it's for John)
- WHEN (deadline if stated)

CRITICAL RULES:
- NEVER invent names, people, or roles - extract ONLY what's in the emails
- NEVER assign tasks to fictional people (no "Mike Johnson", "Tom Patel", etc.)
- If no name is stated, the action is for JOHN
- Extract actual deadlines as stated - do not invent them
- Many corporate emails sound urgent but aren't - use judgment

OUTPUT FORMAT:

## 📋 EXECUTIVE SUMMARY
(2-3 sentences: most critical item + total actionable items)

## 🚨 URGENT - Action Needed Today
(Call-offs, coverage gaps, same-day deadlines)
- Item with specific details

## 🟡 HIGH PRIORITY - This Week  
(Deadlines, submissions, follow-ups due this week)
- Item with specific details

## 🟢 NORMAL - When You Can
(Regular tasks, no rush)
- Item with specific details

## ⚪ FYI - No Action Needed
(Informational only)
- Brief note

Keep it tight. Facts first. No lectures.
PROMPT;
    }

    private function callOllama(string $endpoint, string $model, string $prompt): string
    {
        $url = rtrim($endpoint, '/') . '/api/chat';
        
        $payload = [
            'model' => $model,
            'messages' => [
                ['role' => 'system', 'content' => $this->getSystemPrompt()],
                ['role' => 'user', 'content' => $prompt]
            ],
            'stream' => false,
            'options' => [
                'num_predict' => 4000,
                'temperature' => 0.3
            ]
        ];

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode($payload),
            CURLOPT_TIMEOUT => 180,
            CURLOPT_CONNECTTIMEOUT => 10,
        ]);
        
        $response = curl_exec($ch);
        $error = curl_error($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($error) {
            return "Error: Connection failed - {$error}. Endpoint: {$endpoint}";
        }
        
        if ($httpCode !== 200) {
            $errorBody = substr($response, 0, 500);
            return "Error: HTTP {$httpCode} from Ollama. Response: {$errorBody}";
        }
        
        $data = json_decode($response, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            return "Error: Invalid JSON response from Ollama";
        }
        
        if (isset($data['error'])) {
            return "Error: Ollama error - " . $data['error'];
        }
        
        return $data['message']['content'] ?? 'Error: No content in response';
    }
}
