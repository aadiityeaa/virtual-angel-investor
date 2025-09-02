// --- FINAL CODE WITH EMPTY SLIDE FIX ---

const express = require('express');
const multer = require('multer');
const cors = require('cors');
const pdf = require('pdf-parse');
const mammoth = require('mammoth');
const pptx2json = require('pptx2json');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const path = require('path');
const fs = require('fs');
const os = require('os');

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

const upload = multer({ storage: multer.memoryStorage() });

// --- API KEY CONFIGURATION ---
const apiKey = "";
// -----------------------------

const genAI = new GoogleGenerativeAI(apiKey);
const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
let conversationHistory = [];

app.post('/api/upload', upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).send('No file uploaded.');
  }

  try {
    let text = '';
    const buffer = req.file.buffer;

    if (req.file.mimetype === 'application/pdf') {
      const data = await pdf(buffer);
      text = data.text;
    } else if (req.file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      const result = await mammoth.extractRawText({ buffer });
      text = result.value;
    } else if (req.file.mimetype === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
      const tempFilePath = path.join(os.tmpdir(), req.file.originalname);
      fs.writeFileSync(tempFilePath, buffer);
      
      const pptx = new pptx2json();
      const json = await pptx.toJson(tempFilePath);
      
      const slidesData = json.slides || json;
      // Corrected data handling for empty slides
      text = Object.values(slidesData)
        .map(slide => (slide.text || []).join(' '))
        .join('\n\n');
      
      fs.unlinkSync(tempFilePath);
    } else {
      return res.status(400).send('Unsupported file type.');
    }

    conversationHistory = [
      { role: 'user', parts: [{ text: `Analyze this pitch deck and ask me the first question as if you are an angel investor: ${text}` }] }
    ];

    const result = await model.generateContent({ contents: conversationHistory });
    const firstQuestion = result.response.text();
    
    conversationHistory.push({ role: 'model', parts: [{ text: firstQuestion }] });
    res.json({ question: firstQuestion });

  } catch (error) {
    console.error("Error in /api/upload:", error);
    res.status(500).send('Error processing file.');
  }
});

app.post('/api/continue', async (req, res) => {
  const { answer } = req.body;
  if (!answer) return res.status(400).send('No answer provided.');

  try {
    conversationHistory.push({ role: 'user', parts: [{ text: answer }] });
    const result = await model.generateContent({ contents: conversationHistory });
    const nextQuestion = result.response.text();
    conversationHistory.push({ role: 'model', parts: [{ text: nextQuestion }] });
    res.json({ question: nextQuestion });
  } catch (error) {
    console.error("Error in /api/continue:", error);
    res.status(500).send('Error with AI response.');
  }
});

app.post('/api/finish', async (req, res) => {
  try {
    conversationHistory.push({
      role: 'user',
      parts: [{ text: "Thank you. Please provide a final review with strengths, weaknesses, and suggestions." }]
    });
    const result = await model.generateContent({ contents: conversationHistory });
    const finalReview = result.response.text();
    conversationHistory = [];
    res.json({ review: finalReview });
  } catch (error) {
    console.error("Error in /api/finish:", error);
    res.status(500).send('Error generating final review.');
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});