"use client";

interface ExampleQuestionsProps {
  onQuestionClick: (question: string) => void;
}

const EXAMPLE_QUESTIONS = [
  "What is the expense ratio of HDFC Defence Fund?",
  "Who manages SBI Small Cap Fund?",
  "What is the exit load for Axis Midcap?",
];

export default function ExampleQuestions({ onQuestionClick }: ExampleQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {EXAMPLE_QUESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onQuestionClick(q)}
          className="px-3 py-1.5 text-xs bg-white border border-emerald-200 text-emerald-700 rounded-full hover:bg-emerald-50 hover:border-emerald-400 transition-all duration-150"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
