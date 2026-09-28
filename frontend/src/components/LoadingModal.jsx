import { useState, useEffect } from "react";
import "./LoadingModal.css";

export default function LoadingModal() {
  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
    };
  }, []);
  // const [loadingState, setLoadingState] = useState(0);

  // useEffect(() => {
  //   const timer1 = setTimeout(() => {
  //     setLoadingState(1);
  //   }, 1000);

  //   const timer2 = setTimeout(() => {
  //     setLoadingState(2);
  //   }, 2000);

  //   const timer3 = setTimeout(() => {
  //     setLoadingState(3);
  //   }, 3000);

  //   return () => {
  //     clearTimeout(timer1);
  //     clearTimeout(timer2);
  //     clearTimeout(timer3);
  //   };
  // });

  return (
    <div className="back-drop">
      <div className="center-container">
        <h2 className="loading-title">Building Your Path</h2>
        <div className="progress-bar-container">
          <div className="progress-bar"></div>
        </div>
        <p className="loading-message">Analyzing Skills...</p>
      </div>
    </div>
  );
}
