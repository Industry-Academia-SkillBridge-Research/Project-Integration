function BotQuestionBox({ question }) {
  return (
    <div className="card">
      <h3>Bot Question</h3>
      <p style={{ fontSize: "18px" }}>{question}</p>
    </div>
  );
}

export default BotQuestionBox;
