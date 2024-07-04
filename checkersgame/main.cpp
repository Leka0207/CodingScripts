#include <QTimer>
#include <QPushButton>
#include <QComboBox>
#include <QMessageBox>
#include <QCheckBox>
#include <map>
#include "main.h"
#include "checkersgame.h"
#include "backdrop.h"
#include "boardsquare.h"
#include "gamepiece.h"
#include "ai.h"

namespace CV
{
    std::map<std::pair<char, char>, char> gameBoard;
    std::map<std::pair<char, char>, char> userCreatedBoard;

    int playerTurn = Black;         //Determines which color goes first
    int boardLayout = Standard;
    int gameStatus = ValidMove;     //Displays in right hand corner

    QString movesListString = QString("Red\tBlack\n");  //keeps a list of the moves taken
    QString movesListString2 = QString("Red\tBlack\n"); //for the second column if the first fills up
}
namespace CF
{
    bool editedCustomBoardFlag = false;     //Has a custom board been created?
    bool resetFlag = false;                 //Resets the game
    bool refreshFlag = false;               //Refreshes the scene
    bool redAIFlag = false;
    bool blackAIFlag = false;
    bool playerMovingFlag = false;
}

void drawSceneBoard(QGraphicsScene & scene)
{
    int xOffset = 10;
    int yOffset = 85;

    QGraphicsTextItem * titleText = scene.addText(QString("CHECKERS"));
    titleText->setFont(QFont("Arial", 50));
    titleText->setPos(180, -30);

    QGraphicsTextItem * playerTurnText = scene.addText( (CV::playerTurn == Red) ? QString("Red's Turn") : QString("Black's Turn") );
    playerTurnText->setFont(QFont("Arial", 18));
    playerTurnText->setPos(0, 30);

    //Displays if the move was valid or if a colour has won
    QGraphicsTextItem * displayBar = scene.addText(QString(CV::gameStateVector.at(CV::gameStatus).c_str()));
    displayBar->setFont(QFont("Arial", 18));
    displayBar->setPos(620+75, 20);

    //Displays the moves that have been made this game
    QGraphicsTextItem * movesList = scene.addText(CV::movesListString);
    movesList->setFont(QFont("Arial", 12));
    movesList->setPos(620+75, 150);
    //movesList->setTextWidth(100);
    movesList->setTextInteractionFlags(Qt::TextSelectableByMouse | Qt::TextSelectableByKeyboard);

    if(CV::movesListString.size() >= 694)
    {
        //if the text gets too long, off the window, start a new column
        QGraphicsTextItem * movesList2 = scene.addText(CV::movesListString2);
        movesList2->setFont(QFont("Times", 12));
        movesList2->setPos(800+75, 150);
        movesList2->setTextInteractionFlags(Qt::TextSelectableByMouse | Qt::TextSelectableByKeyboard);
    }

    //reset button
    QPushButton *resetButton = new QPushButton;
    QObject::connect(resetButton, &QPushButton::clicked, [](){CF::resetFlag = true;});
    resetButton->setFont(QFont("Arial", 14));
    resetButton->setGeometry(QRect(695, 75, 120, 30));
    resetButton->setText("Reset");
    scene.addWidget(resetButton);

    //refresh button
    QPushButton *refreshButton = new QPushButton;
    QObject::connect(refreshButton, &QPushButton::clicked, [](){CF::refreshFlag = true;});
    refreshButton->setFont(QFont("Arial", 14));
    refreshButton->setGeometry(QRect(815, 75, 120, 30));
    refreshButton->setText("Refresh \u21BA"); //unicode refresh symbol
    scene.addWidget(refreshButton);

    if(CV::boardLayout == CustomBoardCreate)
    {
        //Only shows play button if in the "Create" tab
        QPushButton *playButton = new QPushButton;
        QObject::connect(playButton, &QPushButton::clicked,
                         [](){CV::boardLayout = CustomBoardPlay; CF::resetFlag = true;});
        playButton->setFont(QFont("Arial", 14));
        playButton->setGeometry(QRect(620 + 75, 30, 240, 45));
        playButton->setText("Play!");
        scene.addWidget(playButton);
    }

    QComboBox *comboBox = new QComboBox;
    comboBox->setFont(QFont("Arial", 14));
    comboBox->setGeometry(620+75, 105, 240/*120*/, 30);
    comboBox->setFrame(true);
    comboBox->addItem(QString("Select Board-Layout  \u25BC"), 0); //unicode down pointer
    comboBox->addItem(QString("Standard"), Standard);
    comboBox->addItem(QString("Kings"), Kings);
    comboBox->addItem(QString("The Akel"), TheAkel);
    comboBox->addItem(QString("TwoRows"), TwoRows);
    comboBox->addItem(QString("Create Custom Board"), CustomBoardCreate);

    if(CF::editedCustomBoardFlag) comboBox->addItem(QString("Play Custom Board"), CustomBoardPlay);
    QObject::connect(comboBox, QOverload<int>::of(&QComboBox::activated),
        [&](int index){ if (index != 0) CV::boardLayout = index; else CV::boardLayout = Standard; });
    scene.addWidget(comboBox);

    QCheckBox *checkboxRedAI = new QCheckBox;
    checkboxRedAI->setFont(QFont("Arial", 14));
    checkboxRedAI->setText("Red AI");
    checkboxRedAI->setGeometry(QRect(630 + 85 + 250, 75, 120, 30));
    checkboxRedAI->setCheckState(CF::redAIFlag ? Qt::Checked : Qt::Unchecked);
    QObject::connect(checkboxRedAI, QOverload<int>::of(&QCheckBox::stateChanged),
        [&](){ CF::redAIFlag = !CF::redAIFlag; CF::refreshFlag = true; });
    scene.addWidget(checkboxRedAI);

    QCheckBox *checkboxBlackAI = new QCheckBox;
    checkboxBlackAI->setFont(QFont("Arial", 14));
    checkboxBlackAI->setText("Black AI");
    checkboxBlackAI->setGeometry(QRect(630 + 85 + 250, 100, 120, 30));
    checkboxBlackAI->setCheckState(CF::blackAIFlag ? Qt::Checked : Qt::Unchecked);
    QObject::connect(checkboxBlackAI, QOverload<int>::of(&QCheckBox::stateChanged),
        [&](){ CF::blackAIFlag = !CF::blackAIFlag; CF::refreshFlag = true;});
    scene.addWidget(checkboxBlackAI);

    //std::map<std::pair<char, char>, QGraphicsItem> visualBoard;
    QGraphicsItem *BackdropItem = new Backdrop(); //can accept drops and return an error if the user misses dropping on a valid square
    scene.addItem(BackdropItem);

    //Prints the black squares of the board
    for (char y = '1'; y <= '8'; y++){
        for (char x = 'a'; x <= 'h'; x++)
        {
            if ((((y - 49) % 2) == 0) == (((x - 97) % 2) == 0))
            {
                QGraphicsItem *boardSquareItem = new BoardSquare((x-97)*75 + 75, 525-(y-49)*75 + yOffset, std::make_pair(x, y));
                //std::cout<<"Placed at "<<x<<","<<y<<std::endl;
                //visualBoard[std::make_pair(x, y)] = boardSquareItem;
                scene.addItem(boardSquareItem);
            }
        }
    }

    //Border rectangle
    scene.addRect(75, yOffset, 600, 600);

    //Draws the row numbers
    for(int i = 0; i < 8; i++)
    {
        QGraphicsSimpleTextItem * number = new QGraphicsSimpleTextItem();
        number->setFont(QFont("Times",40));
        number->setPos(0, (75 * i)+yOffset-10);
        std::string s{};
        s += '8' - i;
        number->setText(QString(s[0]));
        scene.addItem(number);
    }

    //Draws the column letters
    for(int i = 0; i < 8; i++)
    {
        QGraphicsSimpleTextItem * letter = new QGraphicsSimpleTextItem();
        letter->setFont(QFont("Times",40));
        letter->setPos(xOffset + 75 + (75 * i), 600 + yOffset);
        std::string s{};
        s += 'A' + i;
        letter->setText(QString(s[0]));
        scene.addItem(letter);
    }

    if(CF::userCreatingBoardFlag)
    {
        QMessageBox::information(0, QString("Information"),
                                 QString("Welcome to the board layout creator!\n"
                                         "Left click a square to cycle through the colours.\n"
                                         "Right click to promote/demote.\n"
                                         "Press Play when you are ready.\n"
                                         "This board will not be saved if you enter the board creator again."), QMessageBox::Ok);
    }
}
void drawScenePieces(QGraphicsScene & scene, std::map<std::pair<char, char>, char> & gameBoard)
{
    //int xOffset = 10;
    int yOffset = 85;
    QColor colour = Qt::white;
    for (char y = '1'; y <= '8'; y++) {
        for (char x = 'a'; x <= 'h'; x++) {
            if ((((y-49) % 2) == 0) == (((x - 97) % 2) == 0)) { //Helps with the diagonalness of the board
                char piece = gameBoard[std::make_pair(x,y)];
                bool king = false;
                //std::cout<<"Found ["<<piece<<"] at "<<x<<","<<y<<std::endl;
                if (piece == pieces[Black])
                {
                    colour = Qt::black;
                }else if(piece == pieces[BlackKing])
                {
                    colour = Qt::black;
                    king = true;
                }else if (piece == pieces[Red])
                {
                    colour = Qt::red;
                }else if (piece == pieces[RedKing])
                {
                    colour = Qt::red;
                    king = true;
                }else
                {
                    continue;
                }
                //std::cout<<"Placed ["<<(((piece == pieces[2]) || (piece == pieces[1])) ? "x" : "o")<<"] at "<<x<<","<<y<<std::endl;
                QGraphicsItem *gamePieceItem = new GamePiece((x-97)*75 + 75, 525 - (y-49)*75+yOffset, colour, std::make_pair(x, y), king);
                scene.addItem(gamePieceItem);
            }
            //else -> not on board, so doesn't matter
        }
    }
}
void redrawBoard(std::pair<char, char> from, std::pair<char, char> to, QGraphicsScene * scene)
{
    CF::playerMovingFlag = true;
    std::cout<<"Move: "<<char(from.first)<<char(from.second)<<"->"<<char(to.first)<<char(to.second)<<std::endl;
    scene->clear();
    if(CV::gameStatus != RedWin && CV::gameStatus != BlackWin && CV::gameStatus != Draw){ //if the game is running

        CV::gameStatus = takeTurn(CV::gameBoard, std::make_pair(from, to), CV::playerTurn);

        if (CV::gameStatus != ValidMove)
            std::cout<< CV::gameStateVector.at(CV::gameStatus)<<std::endl;

        if(CV::gameStatus != InvalidMove)
        {
            std::stringstream ss {};
            ss << char(toupper(from.first)) << from.second << " -> " << char(toupper(to.first)) << to.second << " ";
            if(CV::gameStatus == RedWin || CV::gameStatus == BlackWin || CV::gameStatus == Draw)
                ss<<"#";
            else if (CV::playerTurn == Red) //If the next player's turn is red
                ss << "\n";
            else
                ss <<"| ";

            if(CV::movesListString.size() < 700)
                CV::movesListString += QString(ss.str().c_str());
            else
                CV::movesListString2 += QString(ss.str().c_str());
        }
    }
    drawSceneBoard(*scene);
    drawScenePieces(*scene, CV::gameBoard);
    CF::playerMovingFlag = false;
}

//For creating custom layouts
void customBoardAddPiece(std::pair<char, char> square, int pieceType)
{
    CV::userCreatedBoard[square] = pieces[pieceType];
    CF::editedCustomBoardFlag = true;
}

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    int width = 700; //620
    int height = 620;
    QGraphicsScene scene(0,0, width, height);
    resetBoard(CV::gameBoard);
    emptyBoard(CV::userCreatedBoard); //for custom created boards
    drawSceneBoard(scene);
    drawScenePieces(scene, CV::gameBoard);

    GraphicsView view(&scene);
    QRectF bounds = scene.itemsBoundingRect();
    bounds.setWidth(bounds.width()*0.9);
    bounds.setHeight(bounds.height()*0.9);

    view.fitInView(bounds, Qt::KeepAspectRatio);

    view.setRenderHint(QPainter::Antialiasing);
    view.setViewportUpdateMode(QGraphicsView::FullViewportUpdate);
    view.setBackgroundBrush(QColor(255,255,255));
    view.setWindowTitle("Checkers");
    view.showMaximized();

    QTimer *timer = new QTimer;
    QObject::connect(timer, &QTimer::timeout, [&scene]()
    {
        if(CF::resetFlag)
        {
            CF::userCreatingBoardFlag = false;
            switch(CV::boardLayout)
            {
            case Standard:
                resetBoard(CV::gameBoard);
                break;
            case Kings:
                customBoardAllKings(CV::gameBoard);
                break;
            case TheAkel:
                customBoardAkel(CV::gameBoard);
                break;
            case TwoRows:
                customBoardEightPiecesEach(CV::gameBoard);
                break;
            case CustomBoardCreate:
                CF::editedCustomBoardFlag = false;
                emptyBoard(CV::gameBoard);
                emptyBoard(CV::userCreatedBoard);
                CF::userCreatingBoardFlag = true;
                break;
            case CustomBoardPlay:
                CV::gameBoard = CV::userCreatedBoard;
                break;
                /*Room for future layouts*/
            }
            checkPromote(CV::gameBoard);
            CV::gameStatus = checkWinStatus(CV::gameBoard, CV::playerTurn); //Protection for custom boards
            CV::playerTurn = Red;
            scene.clear();
            CV::movesListString = QString("Red\tBlack\n");
            CV::movesListString2 = QString("Red\tBlack\n");
            drawSceneBoard(scene);
            drawScenePieces(scene, CV::gameBoard);
            CF::resetFlag = false;
        }
        else if(!CF::playerMovingFlag && !CF::userCreatingBoardFlag
                && CV::gameStatus != RedWin && CV::gameStatus != BlackWin && CV::gameStatus != Draw)
        {
            //AI turn, if enabled
            if(CF::redAIFlag && CV::playerTurn == Red)
            {
                //If it's Red's turn and an AI is controlling it
                auto move = getMoveAI(CV::gameBoard, CV::playerTurn);
                redrawBoard(move.first, move.second, &scene);
            }
            else if(CF::blackAIFlag && CV::playerTurn == Black)
            {
                //If it's Blacks's turn and an AI is controlling it
                auto move = getMoveAI(CV::gameBoard, CV::playerTurn);
                redrawBoard(move.first, move.second, &scene);
            }
        }
        if (CF::refreshFlag)
        {
            if(!CF::userCreatingBoardFlag)
            {
                scene.clear();
                drawSceneBoard(scene);
                drawScenePieces(scene, CV::gameBoard);
                CF::refreshFlag = false;
            }
        }
    });

    timer->start(400); //game speed including AI movement
    view.show();
    return a.exec();
}
