#include "optimization.h"
#include "fretboard.h"
#include <iostream>
#include <algorithm>
#include <cmath>
#include <limits>

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(newNotes)
{
    FindPedalNotes();
}

void Optimization::FindPedalNotes()
{
    // pedálhang: a környező hangok között sokszor ismétlődik, és ő a legmélyebb vagy legmagasabb hang (pl. üres E alatt futó riff)
    // a pedálhangot üres húron szokás játszani, akkor is, ha a kéz feljebb van a fogólapon
    const int pedalRadius = 8;     // ennyi hangot nézünk előre és hátra
    const double pedalShare = 0.3; // a környező hangok legalább ekkora része ez a hang
    const int minWindow = 4;       // ennél kevesebb hangból nem döntünk

    isPedal.assign(notes.size(), false);
    const int n = static_cast<int>(notes.size());
    for (int i = 0; i < n; i++)
    {
        const int from = std::max(0, i - pedalRadius);
        const int to = std::min(n - 1, i + pedalRadius);
        int sameCount = 0;
        int minMidi = notes[i].GetMidiNote();
        int maxMidi = notes[i].GetMidiNote();
        for (int j = from; j <= to; j++)
        {
            const int midi = notes[j].GetMidiNote();
            if (midi == notes[i].GetMidiNote())
            {
                sameCount++;
            }
            minMidi = std::min(minMidi, midi);
            maxMidi = std::max(maxMidi, midi);
        }

        const int windowCount = to - from + 1;
        const bool isExtreme = (notes[i].GetMidiNote() == minMidi || notes[i].GetMidiNote() == maxMidi);
        if (windowCount >= minWindow && isExtreme && sameCount >= pedalShare * windowCount)
        {
            isPedal[i] = true;
        }
    }
}

std::vector<int> Optimization::PossibleHandFrets(const NotePosition &pos) const
{
    std::vector<int> handFrets;

    // üres húrnál nem kell lefogni semmit, a kéz bárhol lehet (közben akár át is helyezkedhet)
    const int maxHandFret = 17;
    if (pos.GetFretIdx() == 0)
    {
        for (int handFret = 1; handFret <= maxHandFret; handFret++)
        {
            handFrets.push_back(handFret);
        }
        return handFrets;
    }

    // a kéz 4 bundot fog át (1 ujj / bund), terpesszel a kisujj még egy bunddal feljebb is elér
    const int stretchSpan = 4;
    for (int handFret = std::max(1, pos.GetFretIdx() - stretchSpan); handFret <= pos.GetFretIdx(); handFret++)
    {
        handFrets.push_back(handFret);
    }
    return handFrets;
}

std::vector<HandState> Optimization::PossibleStates(const size_t noteIdx) const
{
    std::vector<HandState> states;
    for (const auto &pos : FretBoard::GetPositions(notes[noteIdx].GetMidiNote()))
    {
        for (const int handFret : PossibleHandFrets(pos))
        {
            HandState state;
            state.pos = pos;
            state.handFret = handFret;
            states.push_back(state);
        }
    }
    return states;
}

double Optimization::NoteCost(const size_t noteIdx, const HandState &state) const
{
    const double fretWeight = 0.4;      // lefogott hang alapköltsége, az üres húr ennyivel könnyebb
    const int highHandFret = 5;         // ettől a kézpozíciótól számít magasnak a kéz
    const double openHighPenalty = 3.0; // üres húr, miközben a kéz magasan van (nem lehet vibrálni, máshogy szól)

    const int fret = state.pos.GetFretIdx();
    const int stringIdx = state.pos.GetStringIdx();
    double cost = 0.0;

    if (fret == 0)
    {
        // a pedálhang üres húron természetes, ott nincs büntetés
        if (!isPedal[noteIdx])
        {
            cost += TimbreCost(stringIdx);
            if (state.handFret >= highHandFret)
            {
                cost += openHighPenalty;
            }
        }
    }
    else
    {
        cost += fretWeight;
        cost += TimbreCost(stringIdx);
        cost += FingerCost(fret - state.handFret);
    }

    cost += NeckCost(state.pos);
    return cost;
}

double Optimization::FingerCost(const int finger) const
{
    const double ringPenalty = 0.3;    // gyűrűsujj
    const double pinkyPenalty = 1.0;   // a kisujj a leggyengébb
    const double stretchPenalty = 2.5; // 5 bundos terpesz (a kisujj a mutatóujjtól 4 bundra)

    // finger: 0 = mutató, 1 = középső, 2 = gyűrűs, 3 = kisujj, 4 = kisujj terpesszel
    if (finger == 2)
    {
        return ringPenalty;
    }
    if (finger == 3)
    {
        return pinkyPenalty;
    }
    if (finger == 4)
    {
        return pinkyPenalty + stretchPenalty;
    }
    return 0.0;
}

double Optimization::TimbreCost(const int stringIdx) const
{
    // ugyanaz a hang a vastagabb húron teltebben szól, ezért (a kényelmes bundhatárig) azt választjuk
    // a vastag E és az A húr egyformán számít, a D húrtól felfelé húronként drágább
    const double thinStringWeight = 1.0;
    return thinStringWeight * std::max(0, stringIdx - 1);
}

double Optimization::NeckCost(const NotePosition &pos) const
{
    // húronként más a kényelmes felső határ: a vastag húrokon magasan tompa a hang és nehezen elérhető
    const int comfortLimits[6] = {8, 10, 11, 12, 14, 15}; // E, A, D, G, H, e húr
    const double neckWeight = 2.0;                        // bundonként a határ felett

    const int limit = comfortLimits[pos.GetStringIdx()];
    if (pos.GetFretIdx() > limit)
    {
        return neckWeight * (pos.GetFretIdx() - limit);
    }
    return 0.0;
}

double Optimization::TransitionCost(const size_t noteIdx, const HandState &prevState, const HandState &nextState) const
{
    double cost = StringChangeCost(prevState.pos, nextState.pos);
    cost += HandCost(prevState.handFret, nextState.handFret, AvailableTime(noteIdx, nextState));
    return cost;
}

double Optimization::StringChangeCost(const NotePosition &prevPos, const NotePosition &nextPos) const
{
    const double stringWeight = 1.0; // szomszédos húrra váltás (ez a költségek mértékegysége)
    const double skipWeight = 1.75;  // minden átugrott húr (húrugrás, a pengetőkéznek nehezebb)

    const int stringDiff = std::abs(prevPos.GetStringIdx() - nextPos.GetStringIdx());
    if (stringDiff == 0)
    {
        return 0.0;
    }
    return stringWeight + skipWeight * (stringDiff - 1);
}

double Optimization::HandCost(const int prevHandFret, const int nextHandFret, const double availableTime) const
{
    if (prevHandFret == nextHandFret)
    {
        return 0.0;
    }

    const double shiftBase = 4.0;   // minden kézmozgás alapköltsége (a pozíció elhagyása)
    const double handWeight = 1.25; // kézmozgás bundonként

    const int handDiff = std::abs(nextHandFret - prevHandFret);
    double cost = shiftBase + handWeight * handDiff;

    // menzúra mm-ben (a 648 mm a tipikus gitár menzúra)
    const double L = 648.0;

    // a kéz két pozíciójának fizikai távolsága a nyeregtől (mm)
    const double prevHandMm = L * (1.0 - std::pow(2.0, -prevHandFret / 12.0));
    const double nextHandMm = L * (1.0 - std::pow(2.0, -nextHandFret / 12.0));

    // kb 100 mm felett már nagy ugrásnak számít, mm-ként büntetjük
    const double shiftMm = std::abs(prevHandMm - nextHandMm);
    const double maxShiftMm = 100.0;
    const double mmWeight = 0.03;
    if (shiftMm > maxShiftMm)
    {
        cost += (shiftMm - maxShiftMm) * mmWeight;
    }

    return cost * Urgency(availableTime);
}

double Optimization::Urgency(const double availableTime) const
{
    // 0.25 s alatt egyszeres a mozgás költsége, kevesebb időnél drágább, több időnél olcsóbb
    const double referenceTime = 0.25;
    return std::clamp(referenceTime / std::max(availableTime, 0.03), 0.25, 3.0);
}

double Optimization::AvailableTime(const size_t noteIdx, const HandState &nextState) const
{
    // ha a következő hang üres húron szól, a kéz a hang szólása alatt mozoghat (a következő hangig)
    if (nextState.pos.GetFretIdx() == 0)
    {
        if (noteIdx + 1 < notes.size())
        {
            return notes[noteIdx + 1].GetOnset() - notes[noteIdx].GetOnset();
        }
        return 1.0; // az utolsó hang után már nem kell sietni
    }
    return notes[noteIdx].GetOnset() - notes[noteIdx - 1].GetOnset();
}

std::vector<NotePosition> Optimization::RunOptimization()
{
    std::vector<NotePosition> result(notes.size(), NotePosition(0, 0));

    // a gitáron lefoghatatlan hangokat kihagyjuk a keresésből
    std::vector<size_t> playable;
    for (size_t i = 0; i < notes.size(); i++)
    {
        if (FretBoard::GetPositions(notes[i].GetMidiNote()).empty())
        {
            std::cerr << "Nem talalhato lefogas a " << notes[i].GetMidiNote() << " hanghoz!" << std::endl;
        }
        else
        {
            playable.push_back(i);
        }
    }
    if (playable.empty())
    {
        return result;
    }

    // dinamikus programozás a teljes darabra: minden hang minden állapotához (lefogás + kézpozíció)
    // eltároljuk a legolcsóbb odavezető út költségét és azt, hogy melyik előző állapotból jöttünk
    const size_t count = playable.size();
    std::vector<std::vector<HandState>> states(count);
    std::vector<std::vector<double>> bestCosts(count);
    std::vector<std::vector<int>> prevStateIdx(count);

    states[0] = PossibleStates(playable[0]);
    for (const auto &state : states[0])
    {
        bestCosts[0].push_back(NoteCost(playable[0], state));
        prevStateIdx[0].push_back(-1);
    }

    for (size_t t = 1; t < count; t++)
    {
        const size_t noteIdx = playable[t];
        states[t] = PossibleStates(noteIdx);
        bestCosts[t].assign(states[t].size(), std::numeric_limits<double>::max());
        prevStateIdx[t].assign(states[t].size(), -1);

        for (size_t k = 0; k < states[t].size(); k++)
        {
            const double noteCost = NoteCost(noteIdx, states[t][k]);
            for (size_t j = 0; j < states[t - 1].size(); j++)
            {
                const double pathCost = bestCosts[t - 1][j] + TransitionCost(noteIdx, states[t - 1][j], states[t][k]) + noteCost;
                if (pathCost < bestCosts[t][k])
                {
                    bestCosts[t][k] = pathCost;
                    prevStateIdx[t][k] = static_cast<int>(j);
                }
            }
        }
    }

    // a legolcsóbb végállapotból visszafelé követjük az utat
    int bestIdx = 0;
    for (size_t k = 1; k < states[count - 1].size(); k++)
    {
        if (bestCosts[count - 1][k] < bestCosts[count - 1][bestIdx])
        {
            bestIdx = static_cast<int>(k);
        }
    }

    for (int t = static_cast<int>(count) - 1; t >= 0; t--)
    {
        result[playable[t]] = states[t][bestIdx].pos;
        bestIdx = prevStateIdx[t][bestIdx];
    }

    return result;
}
