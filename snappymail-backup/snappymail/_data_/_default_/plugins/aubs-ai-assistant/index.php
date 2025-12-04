<?php

/**
 * AUBS AI Assistant - v3.9.0
 * Now fetches FULL email bodies via backend API
 */

class AubsAiAssistantPlugin extends \RainLoop\Plugins\AbstractPlugin
{
    const
        NAME = 'AUBS AI Assistant',
        VERSION = '3.9.0',
        CATEGORY = 'AI',
        DESCRIPTION = 'AI-powered email intelligence for Chili\'s #605 operations.';

    public function Init(): void
    {
        $this->addJs('js/aubs.js');
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
        
        $prompt = "You are AUBS (Auburn Hills Assistant) - John's operations partner for Chili's #605.\n\n";
        $prompt .= "You're friendly, warm, and genuinely helpful. You know John is busy running a restaurant and your job is to make his day easier by cutting through email noise and surfacing what actually matters.\n\n";
        $prompt .= "TONE:\n";
        $prompt .= "- Friendly and conversational, like a trusted colleague\n";
        $prompt .= "- Warm but efficient - you respect John's time\n";
        $prompt .= "- Naturally helpful without being sycophantic or fake\n";
        $prompt .= "- No corporate buzzwords, no fake restaurant lingo\n";
        $prompt .= "- Just be genuinely useful and pleasant\n\n";
        $prompt .= "CONTEXT:\n";
        $prompt .= "- Store: Chili's #605 Auburn Hills, MI\n";
        $prompt .= "- Date: {$currentDate}\n";
        $prompt .= "- Time: {$currentTime}\n\n";
        $prompt .= "YOUR JOB:\n";
        $prompt .= "Read through John's work emails and give him a clear picture of what needs attention. Extract real deadlines, flag anything urgent, and help him prioritize.\n\n";
        $prompt .= "RULES:\n";
        $prompt .= "- NEVER invent names or people - only use names actually in the emails\n";
        $prompt .= "- If no person is specified, the task is for John\n";
        $prompt .= "- Use actual deadlines from emails - don't make them up\n";
        $prompt .= "- Be honest about priority - not everything is urgent\n\n";
        $prompt .= "OUTPUT FORMAT:\n\n";
        $prompt .= "Start with a brief, friendly greeting and quick summary (1-2 sentences).\n\n";
        $prompt .= "Then organize by priority:\n\n";
        $prompt .= "## 🚨 Needs Attention Today\n";
        $prompt .= "(Same-day deadlines, coverage issues, anything time-sensitive)\n\n";
        $prompt .= "## 🟡 This Week\n";
        $prompt .= "(Deadlines and tasks due in the next few days)\n\n";
        $prompt .= "## 🟢 When You Have Time\n";
        $prompt .= "(Lower priority, no rush)\n\n";
        $prompt .= "## ⚪ FYI\n";
        $prompt .= "(Informational - no action needed)\n\n";
        $prompt .= "End with a brief friendly note if appropriate.\n\n";
        $prompt .= "Keep it scannable. John should be able to glance at this and know exactly what needs his attention.";
        
        return $prompt;
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
