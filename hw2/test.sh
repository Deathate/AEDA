tar xf 312831014.tar
cd 312831014
make
time ./Lab2 ../cases/c1.in ../output/c1.out
time ./Lab2 ../cases/c2.in ../output/c2.out
time ./Lab2 ../cases/c3.in ../output/c3.out
time ./Lab2 ../cases/c4.in ../output/c4.out
time ./Lab2 ../cases/c5.in ../output/c5.out
../SolutionChecker.out ../cases/c1.in ../output/c1.out
../SolutionChecker.out ../cases/c2.in ../output/c2.out
../SolutionChecker.out ../cases/c3.in ../output/c3.out
../SolutionChecker.out ../cases/c4.in ../output/c4.out
../SolutionChecker.out ../cases/c5.in ../output/c5.out
cd ..
