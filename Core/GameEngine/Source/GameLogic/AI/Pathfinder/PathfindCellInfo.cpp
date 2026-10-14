/*
**	Command & Conquer Generals Zero Hour(tm)
**	Copyright 2025 Electronic Arts Inc.
**
**	This program is free software: you can redistribute it and/or modify
**	it under the terms of the GNU General Public License as published by
**	the Free Software Foundation, either version 3 of the License, or
**	(at your option) any later version.
**
**	This program is distributed in the hope that it will be useful,
**	but WITHOUT ANY WARRANTY; without even the implied warranty of
**	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
**	GNU General Public License for more details.
**
**	You should have received a copy of the GNU General Public License
**	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "PreRTS.h" // Required engine types and macros; include first.

#include "GameLogic/Pathfinder/PathfindCellInfo.h"

static UnsignedInt s_cellInfoCapacity = 30000;
static UnsignedInt s_freeCellInfos = 0;
static UnsignedInt s_allocationFailures = 0;

UnsignedInt PathfindCellInfo::getCapacity() { return s_cellInfoCapacity; }
UnsignedInt PathfindCellInfo::getFreeCount() { return s_freeCellInfos; }
UnsignedInt PathfindCellInfo::getAllocationFailures() { return s_allocationFailures; }

PathfindCellInfo *PathfindCellInfo::s_infoArray = nullptr;
PathfindCellInfo *PathfindCellInfo::s_firstFree = nullptr;

#if RETAIL_COMPATIBLE_PATHFINDING
void PathfindCellInfo::forceCleanPathFindCellInfos()
{
	// Preserve retail cleanup for legacy matches; include every extended record.
	const UnsignedInt limit = s_cellInfoCapacity == 30000 ? s_cellInfoCapacity - 1 : s_cellInfoCapacity;
	for (UnsignedInt i = 0; i < limit; i++) {
		s_infoArray[i].m_nextOpen = nullptr;
		s_infoArray[i].m_prevOpen = nullptr;
		s_infoArray[i].m_open = FALSE;
		s_infoArray[i].m_closed = FALSE;
	}
}
#endif

/**
 * Allocates a pool of pathfind cell infos.
 */
void PathfindCellInfo::allocateCellInfos(UnsignedInt capacity)
{
	releaseCellInfos();
	s_cellInfoCapacity = capacity < 30000 ? 30000 : capacity;
	s_freeCellInfos = s_cellInfoCapacity;
	s_allocationFailures = 0;
	s_infoArray = MSGNEW("PathfindCellInfo") PathfindCellInfo[s_cellInfoCapacity];	// pool[]ify
	s_infoArray[s_cellInfoCapacity-1].m_pathParent = nullptr;
	s_infoArray[s_cellInfoCapacity-1].m_isFree = true;
	s_firstFree = s_infoArray;
	for (UnsignedInt i=0; i<s_cellInfoCapacity-1; i++) {
		s_infoArray[i].m_pathParent = &s_infoArray[i+1];
		s_infoArray[i].m_isFree = true;
	}
}

/**
 * Releases a pool of pathfind cell infos.
 */
void PathfindCellInfo::releaseCellInfos()
{
	if (s_infoArray==nullptr) {
		return; // haven't allocated any yet.
	}
	Int count=0;
	while (s_firstFree) {
		count++;
		DEBUG_ASSERTCRASH(s_firstFree->m_isFree, ("Should be freed."));
		s_firstFree = s_firstFree->m_pathParent;
	}
	DEBUG_ASSERTCRASH(count==s_cellInfoCapacity, ("Error - Allocated cellinfos."));
	delete[] s_infoArray;
	s_infoArray = nullptr;
	s_firstFree = nullptr;
	s_freeCellInfos = 0;
}

/**
 * Gets a pathfindcellinfo.
 */
PathfindCellInfo *PathfindCellInfo::getACellInfo(PathfindCell *cell,const ICoord2D &pos)
{
	PathfindCellInfo *info = s_firstFree;
	if (s_firstFree) {
		--s_freeCellInfos;
		DEBUG_ASSERTCRASH(s_firstFree->m_isFree, ("Should be freed."));
		s_firstFree = s_firstFree->m_pathParent;
		info->m_isFree = false;  // Just allocated it.
		info->m_cell = cell;
		info->m_pos = pos;

		info->m_nextOpen = nullptr;
		info->m_prevOpen = nullptr;
		info->m_pathParent = nullptr;
		info->m_costSoFar = 0;
		info->m_totalCost = 0;
		info->m_open = 0;
		info->m_closed = 0;
		info->m_obstacleID = INVALID_ID;
		info->m_goalUnitID = INVALID_ID;
		info->m_posUnitID = INVALID_ID;
		info->m_goalAircraftID = INVALID_ID;
		info->m_obstacleIsFence = false;
		info->m_obstacleIsTransparent = false;
		info->m_blockedByAlly = false;
	} else {
		++s_allocationFailures;
	}
	return info;
}

/**
 * Returns a pathfindcellinfo.
 */
void PathfindCellInfo::releaseACellInfo(PathfindCellInfo *theInfo)
{
	DEBUG_ASSERTCRASH(!theInfo->m_isFree, ("Shouldn't be free."));
	//@ todo -fix this assert on usa04.  jba.
	//DEBUG_ASSERTCRASH(theInfo->m_obstacleID==0, ("Shouldn't be obstacle."));
	theInfo->m_pathParent = s_firstFree;
	s_firstFree = theInfo;
	s_firstFree->m_isFree = true;
	++s_freeCellInfos;
}
