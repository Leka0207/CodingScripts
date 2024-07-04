#ifndef MAIN_H
#define MAIN_H
#include <QApplication>
#include <QGraphicsView>
#include <QGraphicsSceneDragDropEvent>

namespace CV{static const std::vector<std::string> gameStateVector = {"Invalid Move", "" /*Valid Move*/, "Red Wins", "Black Wins", "Draw", };}
namespace CF{static bool userCreatingBoardFlag = false;}

typedef enum BoardLayout{
    Standard = 1,
    Kings,
    TheAkel,
    TwoRows,
    CustomBoardCreate,
    CustomBoardPlay
}BoardLayout;

class GraphicsView : public QGraphicsView
{
public:
    GraphicsView(QGraphicsScene *scene) : QGraphicsView(scene){
        setAcceptDrops(true);
    }
public slots:
    //TBA?
    void zoomIn() { scale(1.2, 1.2); }
    void zoomOut() { scale(1 / 1.2, 1 / 1.2); }

private:
    void dragEnterEvent(QGraphicsSceneDragDropEvent *event){
        Q_UNUSED(event);
    }
    void dragLeaveEvent(QGraphicsSceneDragDropEvent *event){
        Q_UNUSED(event);
        update();
    }
    void dropEvent(QGraphicsSceneDragDropEvent *event){
        event->setAccepted(true);
        update();
    }
};

int main(int argc, char *argv[]);
void drawSceneBoard( QGraphicsScene & scene);
void drawScenePieces(QGraphicsScene & scene, std::map<std::pair<char, char>, char> & gameBoard);
void redrawBoard(std::pair<char, char> from, std::pair<char, char> to, QGraphicsScene * scene);
void customBoardAddPiece(std::pair<char, char> square, int pieceType);
#endif
