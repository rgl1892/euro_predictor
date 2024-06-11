var score = document.querySelectorAll(`[group]`)
// console.log(score);

for (i=0;i<score.length;i++) {
    console.log(score[i].attributes.match.value)
}