import React from 'react';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import {gettext} from 'utils';
import {formatNavigationDate, getPrevious, getNext} from 'agenda/utils';


function AgendaDateNavigation({selectDate, activeDate, activeGrouping}) {
    return (<div className='d-none d-lg-flex align-items-center mr-3'>
        <span className='mr-3'>{formatNavigationDate(activeDate, activeGrouping)}</span>
        <button
            type='button'
            className='btn btn-outline-primary btn-sm mr-3'
            onClick={() => selectDate(Date.now(), 'day')}>
            {gettext('Today')}
        </button>
        <button
            type='button'
            className='icon-button icon-button--small mr-2'
            onClick={() => selectDate(getPrevious(activeDate, activeGrouping), activeGrouping)}>
            <i className='icon--arrow-right icon--rotate-180'></i>
        </button>
        <button
            type='button'
            className='icon-button icon-button--small mr-3'
            onClick={() => selectDate(getNext(activeDate, activeGrouping), activeGrouping)}>
            <i className='icon--arrow-right'></i>
        </button>
        <button
            type='button'
            className={classnames('btn btn-outline-primary btn-sm mr-2', {'active': activeGrouping === 'day'})}
            onClick={() => selectDate(activeDate, 'day')}>
            {gettext('D')}
        </button>
        <button
            type='button'
            className={classnames('btn btn-outline-primary btn-sm mr-2', {'active': activeGrouping === 'week'})}
            onClick={() => selectDate(activeDate, 'week')}>
            {gettext('W')}
        </button>
        <button
            type='button'
            className={classnames('btn btn-outline-primary btn-sm', {'active': activeGrouping === 'month'})}
            onClick={() => selectDate(activeDate, 'month')}>
            {gettext('M')}
        </button>
    </div>);
}

AgendaDateNavigation.propTypes = {
    selectDate: PropTypes.func,
    activeDate: PropTypes.number,
    activeGrouping: PropTypes.string,
};

export default AgendaDateNavigation;
