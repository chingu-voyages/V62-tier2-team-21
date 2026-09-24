export function validateInput(careerGoal, pastExperience) {
  const errors = {
    careerGoal: "",
    pastExperience: "",
  };

  if (careerGoal.trim() === "") {
    errors.careerGoal = "Please enter your career goal.";
  }

  if (pastExperience.trim() === "") {
    errors.pastExperience = "Please enter your past experience.";
  }

  return errors;
}
