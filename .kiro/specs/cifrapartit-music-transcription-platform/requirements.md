# Requirements Document

## Introduction

CifraPartit é uma plataforma web profissional de transcrição musical baseada em IA que transforma áudio e vídeo em partituras, tablaturas e arquivos MIDI. O sistema permite que músicos, compositores, produtores, estudantes e educadores musicais transcrevam automaticamente músicas usando modelos de aprendizado de máquina especializados por instrumento, editem as transcrições em um editor online integrado e exportem os resultados em múltiplos formatos profissionais.

## Glossary

- **CifraPartit_Platform**: O sistema web completo incluindo frontend, backend, motor de IA e banco de dados
- **Transcription_Engine**: O componente de IA/ML responsável por analisar áudio e gerar notação musical
- **Audio_Input**: Arquivo de áudio ou vídeo fornecido pelo usuário (MP3, WAV, MP4, etc.)
- **Score_Editor**: Interface web para visualização e edição de partituras e tablaturas
- **User**: Qualquer pessoa que acessa a plataforma (autenticada ou não)
- **Registered_User**: Usuário com conta criada na plataforma
- **Pro_User**: Usuário com assinatura paga ativa
- **Free_User**: Usuário sem assinatura paga
- **Transcription**: Resultado do processamento de áudio contendo notação musical
- **Songbook**: Coleção pessoal de transcrições salvas de um usuário
- **Instrument_Model**: Modelo de IA especializado para um tipo específico de instrumento
- **Export_Format**: Formato de arquivo de saída (PDF, MusicXML, MIDI, GPX, GP5)
- **Browser_Recorder**: Componente que captura áudio diretamente do microfone do navegador
- **YouTube_Importer**: Componente que extrai áudio de URLs do YouTube
- **Piano_Roll**: Visualização gráfica de notas musicais em grade temporal
- **Tablature**: Notação musical específica para instrumentos de corda mostrando posições dos dedos
- **Polyphonic_Transcription**: Transcrição de múltiplas notas/vozes simultâneas
- **OCR_Scanner**: Componente de reconhecimento óptico de partituras em imagem
- **Key_Detector**: Componente que identifica a tonalidade de uma música
- **Processing_Queue**: Fila assíncrona para processamento de transcrições

## Requirements

### Requirement 1: Audio and Video Input Management

**User Story:** Como músico, eu quero enviar áudio ou vídeo de diferentes fontes, para que eu possa transcrever músicas de qualquer origem.

#### Acceptance Criteria

1. WHEN a User uploads an audio file in MP3 format, THE CifraPartit_Platform SHALL accept and store the Audio_Input
2. WHEN a User uploads an audio file in WAV format, THE CifraPartit_Platform SHALL accept and store the Audio_Input
3. WHEN a User uploads a video file in MP4 format, THE CifraPartit_Platform SHALL extract the audio track and store it as Audio_Input
4. WHEN a User uploads a file larger than 100MB, THE CifraPartit_Platform SHALL reject the upload and display an error message
5. WHEN a User uploads a file in an unsupported format, THE CifraPartit_Platform SHALL reject the upload and display a list of supported formats
6. THE CifraPartit_Platform SHALL support audio file formats: MP3, WAV, FLAC, OGG, M4A, AAC
7. THE CifraPartit_Platform SHALL support video file formats: MP4, AVI, MOV, WEBM

### Requirement 2: Browser-Based Audio Recording

**User Story:** Como músico, eu quero gravar áudio diretamente no navegador, para que eu possa transcrever minhas próprias performances sem precisar de arquivos externos.

#### Acceptance Criteria

1. WHEN a User clicks the record button, THE Browser_Recorder SHALL request microphone permission
2. WHEN microphone permission is granted, THE Browser_Recorder SHALL begin capturing audio
3. WHILE recording is active, THE Browser_Recorder SHALL display recording duration in real-time
4. WHEN a User clicks the stop button, THE Browser_Recorder SHALL stop capturing and save the audio as Audio_Input
5. WHEN recording duration exceeds 10 minutes, THE Browser_Recorder SHALL automatically stop and save the audio
6. IF microphone permission is denied, THEN THE Browser_Recorder SHALL display an error message explaining permission requirements

### Requirement 3: YouTube Audio Import

**User Story:** Como músico, eu quero importar áudio de vídeos do YouTube, para que eu possa transcrever músicas disponíveis online.

#### Acceptance Criteria

1. WHEN a User provides a valid YouTube URL, THE YouTube_Importer SHALL extract the audio track
2. WHEN audio extraction completes, THE YouTube_Importer SHALL store the audio as Audio_Input
3. WHEN a User provides an invalid YouTube URL, THE YouTube_Importer SHALL display an error message
4. IF the YouTube video is longer than 15 minutes, THEN THE YouTube_Importer SHALL extract only the first 15 minutes
5. WHEN YouTube extraction fails due to restrictions, THE YouTube_Importer SHALL display a message suggesting direct file upload

### Requirement 4: AI-Powered Music Transcription

**User Story:** Como músico, eu quero que o sistema transcreva automaticamente o áudio em notação musical, para que eu possa obter partituras sem transcrever manualmente.

#### Acceptance Criteria

1. WHEN Audio_Input is submitted for transcription, THE Transcription_Engine SHALL detect notes, melody, rhythm and chords
2. WHEN processing Audio_Input, THE Transcription_Engine SHALL perform Polyphonic_Transcription for multiple simultaneous notes
3. WHEN transcription completes, THE Transcription_Engine SHALL generate a Transcription object containing musical notation data
4. WHEN transcription processing time exceeds 5 minutes, THE Transcription_Engine SHALL send a progress notification to the User
5. IF transcription fails due to poor audio quality, THEN THE Transcription_Engine SHALL return an error message with quality improvement suggestions
6. THE Transcription_Engine SHALL process audio asynchronously using the Processing_Queue
7. WHEN transcription is queued, THE CifraPartit_Platform SHALL provide the User with a unique tracking identifier

### Requirement 5: Instrument-Specific Transcription Models

**User Story:** Como músico, eu quero selecionar o tipo de instrumento antes da transcrição, para que eu obtenha resultados mais precisos para cada instrumento.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL provide Instrument_Model options: piano, guitar, bass, vocals, drums, strings, woodwinds, brass
2. WHEN a User selects an Instrument_Model, THE Transcription_Engine SHALL use the corresponding specialized AI model
3. WHERE guitar Instrument_Model is selected, THE Transcription_Engine SHALL generate both standard notation and Tablature
4. WHERE bass Instrument_Model is selected, THE Transcription_Engine SHALL generate both standard notation and Tablature
5. WHERE drums Instrument_Model is selected, THE Transcription_Engine SHALL generate percussion notation
6. WHERE piano Instrument_Model is selected, THE Transcription_Engine SHALL generate grand staff notation with treble and bass clefs

### Requirement 6: Online Score Editor

**User Story:** Como músico, eu quero visualizar e editar a transcrição no navegador, para que eu possa corrigir erros e ajustar a notação.

#### Acceptance Criteria

1. WHEN a Transcription is completed, THE Score_Editor SHALL display the musical notation in standard staff format
2. THE Score_Editor SHALL allow Users to add, delete, and modify individual notes
3. THE Score_Editor SHALL allow Users to change time signatures, key signatures, and tempo markings
4. THE Score_Editor SHALL provide playback functionality for the displayed notation
5. WHEN a User modifies a note, THE Score_Editor SHALL update the display within 100ms
6. THE Score_Editor SHALL support undo and redo operations for all editing actions
7. THE Score_Editor SHALL auto-save changes every 30 seconds while editing is active

### Requirement 7: Piano Roll Visualization

**User Story:** Como produtor musical, eu quero visualizar a transcrição em formato Piano Roll, para que eu possa ver as notas em uma grade temporal similar a DAWs.

#### Acceptance Criteria

1. THE Score_Editor SHALL provide a Piano_Roll view option
2. WHEN Piano_Roll view is selected, THE Score_Editor SHALL display notes as horizontal bars on a pitch-time grid
3. THE Piano_Roll SHALL allow Users to drag notes horizontally to change timing
4. THE Piano_Roll SHALL allow Users to drag notes vertically to change pitch
5. THE Piano_Roll SHALL allow Users to resize note bars to change duration
6. WHEN a User switches between standard notation and Piano_Roll views, THE Score_Editor SHALL preserve all note data

### Requirement 8: Automatic Tablature Generation

**User Story:** Como guitarrista, eu quero que o sistema gere automaticamente tablaturas, para que eu possa ler a música no formato específico de guitarra.

#### Acceptance Criteria

1. WHERE guitar or bass Instrument_Model is selected, THE Transcription_Engine SHALL automatically generate Tablature
2. THE Tablature SHALL display fret numbers on six strings for guitar
3. THE Tablature SHALL display fret numbers on four strings for bass
4. THE Score_Editor SHALL allow Users to toggle between standard notation and Tablature views
5. WHEN a User edits a note in standard notation, THE Score_Editor SHALL automatically update the corresponding Tablature
6. WHEN a User edits a fret position in Tablature, THE Score_Editor SHALL automatically update the corresponding standard notation

### Requirement 9: Multi-Format Export

**User Story:** Como músico, eu quero exportar transcrições em diferentes formatos, para que eu possa usar os resultados em outros softwares musicais.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL support Export_Format options: PDF, MusicXML, MIDI, GPX, GP5
2. WHEN a User requests PDF export, THE CifraPartit_Platform SHALL generate a printable score document
3. WHEN a User requests MusicXML export, THE CifraPartit_Platform SHALL generate a valid MusicXML file compatible with notation software
4. WHEN a User requests MIDI export, THE CifraPartit_Platform SHALL generate a MIDI file containing all note and timing information
5. WHEN a User requests GPX export, THE CifraPartit_Platform SHALL generate a Guitar Pro 7 compatible file
6. WHEN a User requests GP5 export, THE CifraPartit_Platform SHALL generate a Guitar Pro 5 compatible file
7. WHEN export generation completes, THE CifraPartit_Platform SHALL provide a download link valid for 24 hours

### Requirement 10: User Registration and Authentication

**User Story:** Como músico, eu quero criar uma conta, para que eu possa salvar minhas transcrições e acessá-las de qualquer dispositivo.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL allow Users to register with email and password
2. WHEN a User registers, THE CifraPartit_Platform SHALL send a verification email
3. WHEN a User clicks the verification link, THE CifraPartit_Platform SHALL activate the account
4. THE CifraPartit_Platform SHALL allow Registered_Users to log in with email and password
5. THE CifraPartit_Platform SHALL allow Registered_Users to reset passwords via email
6. WHEN login credentials are invalid, THE CifraPartit_Platform SHALL display an error message without revealing which field is incorrect
7. THE CifraPartit_Platform SHALL implement rate limiting of 5 failed login attempts per 15 minutes per IP address

### Requirement 11: Personal Songbook Management

**User Story:** Como músico registrado, eu quero organizar minhas transcrições em um Songbook pessoal, para que eu possa encontrar e gerenciar facilmente meu trabalho.

#### Acceptance Criteria

1. WHEN a Registered_User saves a Transcription, THE CifraPartit_Platform SHALL add it to the User's Songbook
2. THE Songbook SHALL display transcriptions with title, instrument type, creation date, and duration
3. THE Songbook SHALL allow Registered_Users to search transcriptions by title
4. THE Songbook SHALL allow Registered_Users to filter transcriptions by instrument type
5. THE Songbook SHALL allow Registered_Users to delete transcriptions
6. WHEN a Registered_User deletes a Transcription, THE CifraPartit_Platform SHALL remove it permanently after confirmation
7. THE Songbook SHALL synchronize across all devices where the Registered_User is logged in

### Requirement 12: Free Tier Limitations

**User Story:** Como usuário gratuito, eu quero experimentar o serviço com limitações, para que eu possa avaliar a qualidade antes de assinar.

#### Acceptance Criteria

1. WHERE a User is a Free_User, THE CifraPartit_Platform SHALL limit transcription duration to 30 seconds
2. WHERE a User is a Free_User, THE CifraPartit_Platform SHALL allow a maximum of 3 transcriptions per day
3. WHERE a User is a Free_User, THE CifraPartit_Platform SHALL allow export only in PDF format
4. WHEN a Free_User attempts to transcribe audio longer than 30 seconds, THE CifraPartit_Platform SHALL process only the first 30 seconds
5. WHEN a Free_User reaches the daily transcription limit, THE CifraPartit_Platform SHALL display a message promoting the Pro subscription
6. WHERE a User is not a Registered_User, THE CifraPartit_Platform SHALL allow only 1 transcription per session without saving

### Requirement 13: Pro Subscription Features

**User Story:** Como músico profissional, eu quero assinar o plano Pro, para que eu possa transcrever músicas completas sem limitações.

#### Acceptance Criteria

1. WHERE a User is a Pro_User, THE CifraPartit_Platform SHALL allow transcription of audio up to 15 minutes duration
2. WHERE a User is a Pro_User, THE CifraPartit_Platform SHALL allow unlimited transcriptions per day
3. WHERE a User is a Pro_User, THE CifraPartit_Platform SHALL allow export in all Export_Format options
4. WHERE a User is a Pro_User, THE CifraPartit_Platform SHALL provide priority processing in the Processing_Queue
5. THE CifraPartit_Platform SHALL allow Registered_Users to upgrade to Pro_User status via payment
6. WHEN a Pro_User subscription expires, THE CifraPartit_Platform SHALL revert the user to Free_User limitations

### Requirement 14: Sheet Music OCR Scanner (Scan2Notes)

**User Story:** Como músico, eu quero escanear partituras em papel, para que eu possa converter notação física em formato digital editável.

#### Acceptance Criteria

1. WHEN a User uploads an image of sheet music, THE OCR_Scanner SHALL recognize musical notation elements
2. THE OCR_Scanner SHALL detect notes, rests, clefs, time signatures, and key signatures from images
3. WHEN OCR processing completes, THE OCR_Scanner SHALL generate an editable Transcription
4. THE OCR_Scanner SHALL support image formats: JPG, PNG, PDF
5. IF the image quality is insufficient for accurate recognition, THEN THE OCR_Scanner SHALL return an error message with quality improvement suggestions
6. THE OCR_Scanner SHALL process images asynchronously using the Processing_Queue

### Requirement 15: Melody Scanner

**User Story:** Como compositor, eu quero extrair apenas a melodia principal de uma música, para que eu possa focar na linha melódica sem harmonia.

#### Acceptance Criteria

1. WHEN a User selects melody-only transcription mode, THE Transcription_Engine SHALL isolate the dominant melodic line
2. THE Transcription_Engine SHALL suppress accompaniment and harmonic elements in melody-only mode
3. WHEN melody extraction completes, THE Transcription_Engine SHALL generate a single-voice Transcription
4. THE CifraPartit_Platform SHALL allow Users to toggle between full transcription and melody-only views

### Requirement 16: Key Detection

**User Story:** Como músico, eu quero que o sistema identifique automaticamente a tonalidade da música, para que eu possa transpor ou analisar harmonicamente.

#### Acceptance Criteria

1. WHEN Audio_Input is processed, THE Key_Detector SHALL analyze the harmonic content
2. WHEN key detection completes, THE Key_Detector SHALL return the detected key signature (e.g., C major, A minor)
3. THE Score_Editor SHALL display the detected key signature in the notation
4. THE Score_Editor SHALL allow Users to manually override the detected key signature
5. WHEN a User changes the key signature, THE Score_Editor SHALL offer to transpose all notes accordingly

### Requirement 17: Instrument-Specific Landing Pages

**User Story:** Como guitarrista, eu quero acessar uma página específica para guitarra, para que eu veja informações e exemplos relevantes ao meu instrumento.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL provide dedicated landing pages at URLs: /piano, /guitarra, /vocal, /bateria, /cordas, /sopro
2. WHEN a User accesses an instrument-specific page, THE CifraPartit_Platform SHALL display examples and features relevant to that instrument
3. WHEN a User accesses an instrument-specific page, THE CifraPartit_Platform SHALL pre-select the corresponding Instrument_Model for transcription
4. THE instrument-specific pages SHALL include audio samples demonstrating transcription quality for that instrument

### Requirement 18: Responsive Design

**User Story:** Como músico que usa diferentes dispositivos, eu quero que o site funcione bem em desktop, tablet e celular, para que eu possa transcrever músicas em qualquer lugar.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL render correctly on desktop screens with minimum width of 1024px
2. THE CifraPartit_Platform SHALL render correctly on tablet screens with width between 768px and 1023px
3. THE CifraPartit_Platform SHALL render correctly on mobile screens with width between 320px and 767px
4. WHEN screen width is below 768px, THE Score_Editor SHALL adapt the interface for touch interaction
5. THE CifraPartit_Platform SHALL support touch gestures for zooming and panning on mobile devices

### Requirement 19: Copyright and Attribution

**User Story:** Como proprietário da plataforma, eu quero que os direitos autorais sejam claramente exibidos, para que a autoria de Ezequiel Ribeiro seja reconhecida.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL display "© 2024 Ezequiel Ribeiro. Todos os direitos reservados." in the footer of all pages
2. THE CifraPartit_Platform SHALL include a credits page accessible from the footer
3. THE credits page SHALL state that CifraPartit is created and owned by Ezequiel Ribeiro
4. THE credits page SHALL clarify that CifraPartit is not affiliated with or endorsed by Klang.io
5. THE CifraPartit_Platform SHALL include copyright metadata in all exported PDF files

### Requirement 20: SEO Optimization

**User Story:** Como proprietário da plataforma, eu quero que o site seja otimizado para motores de busca, para que músicos possam encontrar o CifraPartit facilmente.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL include descriptive meta tags on all public pages
2. THE CifraPartit_Platform SHALL generate a sitemap.xml file listing all public pages
3. THE CifraPartit_Platform SHALL implement semantic HTML5 markup
4. THE CifraPartit_Platform SHALL include Open Graph tags for social media sharing
5. THE CifraPartit_Platform SHALL achieve a Lighthouse SEO score of at least 90
6. THE CifraPartit_Platform SHALL implement structured data markup for music-related content

### Requirement 21: Performance and Scalability

**User Story:** Como usuário, eu quero que o site carregue rapidamente e processe transcrições eficientemente, para que eu possa trabalhar sem frustrações.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL load the home page in less than 2 seconds on a 4G connection
2. THE Score_Editor SHALL render transcriptions with up to 500 notes within 1 second
3. THE Processing_Queue SHALL handle at least 10 concurrent transcription jobs
4. WHEN server load exceeds 80% capacity, THE CifraPartit_Platform SHALL queue new transcription requests
5. THE CifraPartit_Platform SHALL implement caching for static assets with a cache lifetime of 7 days
6. THE CifraPartit_Platform SHALL compress all text-based responses using gzip or brotli

### Requirement 22: Error Handling and User Feedback

**User Story:** Como usuário, eu quero receber mensagens claras quando algo der errado, para que eu saiba como resolver problemas.

#### Acceptance Criteria

1. WHEN an error occurs during transcription, THE CifraPartit_Platform SHALL display a user-friendly error message
2. WHEN an error occurs, THE CifraPartit_Platform SHALL log detailed error information for debugging
3. IF Audio_Input quality is too low for transcription, THEN THE CifraPartit_Platform SHALL suggest specific improvements (e.g., "Reduce background noise")
4. WHEN a network error occurs, THE CifraPartit_Platform SHALL display a retry option
5. WHEN Processing_Queue wait time exceeds 2 minutes, THE CifraPartit_Platform SHALL display estimated wait time to the User

### Requirement 23: Data Privacy and Security

**User Story:** Como usuário registrado, eu quero que meus dados e transcrições sejam protegidos, para que minha privacidade seja respeitada.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL encrypt all passwords using bcrypt with a cost factor of at least 12
2. THE CifraPartit_Platform SHALL transmit all data over HTTPS connections
3. THE CifraPartit_Platform SHALL store Audio_Input files with access restricted to the owning User
4. WHEN a Registered_User deletes their account, THE CifraPartit_Platform SHALL permanently delete all associated data within 30 days
5. THE CifraPartit_Platform SHALL implement CSRF protection for all state-changing operations
6. THE CifraPartit_Platform SHALL sanitize all user inputs to prevent XSS attacks

### Requirement 24: Help and Documentation

**User Story:** Como novo usuário, eu quero acessar documentação e tutoriais, para que eu possa aprender a usar a plataforma efetivamente.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL provide a "Como Funciona" page explaining the transcription process
2. THE CifraPartit_Platform SHALL provide a FAQ page answering common questions
3. THE FAQ page SHALL include at least 15 frequently asked questions with detailed answers
4. THE CifraPartit_Platform SHALL provide video tutorials demonstrating key features
5. THE CifraPartit_Platform SHALL include tooltips on complex interface elements in the Score_Editor
6. THE CifraPartit_Platform SHALL provide a contact form for user support requests

### Requirement 25: Testimonials and Social Proof

**User Story:** Como visitante, eu quero ver depoimentos de outros usuários, para que eu possa confiar na qualidade do serviço.

#### Acceptance Criteria

1. THE CifraPartit_Platform SHALL display a testimonials section on the home page
2. THE testimonials section SHALL include at least 6 user testimonials
3. WHEN displaying testimonials, THE CifraPartit_Platform SHALL show the user's name, role (e.g., "Guitarrista Profissional"), and testimonial text
4. THE CifraPartit_Platform SHALL allow Registered_Users to submit testimonials for review
5. THE CifraPartit_Platform SHALL display testimonials in a rotating carousel format
